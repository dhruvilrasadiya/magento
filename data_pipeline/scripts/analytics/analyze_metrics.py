from collections import defaultdict, Counter
from datetime import datetime, timedelta
from statistics import mean
from scripts.product_data.fetch_dge_products_for_mapping import DGEClient


def analyze_magento_orders(orders: list) -> dict:
    insights = {}

    # Helper containers
    revenue_by_date = defaultdict(float)
    orders_by_payment = Counter()
    orders_over_time = defaultdict(int)
    revenue_by_product = defaultdict(float)
    product_qty = defaultdict(int)
    product_price_list = defaultdict(list)
    cost_vs_price = []
    customer_purchases = defaultdict(float)
    guest_vs_registered = Counter()
    billing_countries = Counter()
    shipping_countries = Counter()
    order_status_stuck = []
    processing_times = []
    refunded_orders = 0
    cancelled_orders = 0
    free_shipping_count = 0
    shipping_destinations = Counter()
    shipping_methods = Counter()

    for order in orders:
        created_at = datetime.fromisoformat(
            order.get("created_at", "").replace("Z", "+00:00")
        )
        updated_at = datetime.fromisoformat(
            order.get("updated_at", "").replace("Z", "+00:00")
        )

        # 1. Sales & Revenue Analytics
        base_grand_total = order.get("base_grand_total", 0)
        revenue_by_date[created_at.date()] += base_grand_total
        orders_by_payment[order.get("payment", {}).get("method", "unknown")] += 1
        orders_over_time[created_at.date()] += 1
        total_tax = order.get("tax_amount", 0)

        # Revenue by product
        for item in order.get("items", []):
            sku = item.get("sku", "unknown")
            product_qty[sku] += item.get("qty_ordered", 0)
            revenue_by_product[sku] += item.get("row_total", 0)
            product_price_list[sku].append(item.get("price", 0))
            cost = item.get("base_cost", 0)
            price = item.get("base_price", 0)
            if cost and price:
                cost_vs_price.append((cost, price))

        # 2. Customer Analysis
        guest = order.get("customer_is_guest", True)
        guest_vs_registered["guest" if guest else "registered"] += 1
        customer_email = order.get("customer_email", "unknown")
        customer_purchases[customer_email] += base_grand_total

        billing = order.get("billing_address", {})
        shipping = order.get("shipping_address", {})
        billing_countries[billing.get("country_id", "unknown")] += 1
        shipping_countries[shipping.get("country_id", "unknown")] += 1

        # 3. Order Status & Processing
        if order.get("status") in ["pending", "processing"]:
            order_status_stuck.append(order.get("increment_id", "unknown"))
        processing_times.append((updated_at - created_at).total_seconds())

        if order.get("total_refunded", 0) > 0:
            refunded_orders += 1
        if order.get("status") == "canceled":
            cancelled_orders += 1

        # 4. Shipping & Fulfillment
        shipping_desc = order.get("shipping_description", "")
        if "free" in shipping_desc.lower():
            free_shipping_count += 1

        shipping_destinations[
            f"{shipping.get('city', '')}, {shipping.get('country_id', '')}"
        ] += 1
        shipping_methods[order.get("shipping", {}).get("method", "unknown")] += 1

    if orders:
        highest_order = max(orders, key=lambda o: o.get("base_grand_total", 0))
        lowest_order = min(orders, key=lambda o: o.get("base_grand_total", 0))
        highest_value = highest_order.get("base_grand_total", 0)
        lowest_value = lowest_order.get("base_grand_total", 0)
        highest_id = highest_order.get("items")[0].get("order_id", "unknown")
        lowest_id = lowest_order.get("items")[0].get("order_id", "unknown")

    # Generate insights for each section
    insights["1. Sales & Revenue Analytics"] = (
        f"Total revenue was ${sum(revenue_by_date.values()):,.2f}, with peak sales on "
        f"{max(revenue_by_date, key=revenue_by_date.get)}. Most orders used payment methods such as: "
        f"{', '.join(f'{k} ({v})' for k, v in orders_by_payment.items())}. There were "
        f"{sum(orders_over_time.values())} orders placed overall. "
        f"Total tax collected: ${sum(order.get('tax_amount', 0) for order in orders):,.2f}. "
        f"Top earning products include: {', '.join(sorted(revenue_by_product, key=revenue_by_product.get, reverse=True)[:3])}."
        f"The biggest order was #{highest_id} worth ${highest_value:,.2f}, while the lowest order was #{lowest_id} at ${lowest_value:,.2f}."
    )

    top_customers = sorted(
        customer_purchases.items(), key=lambda x: x[1], reverse=True
    )[:3]
    insights["2. Customer Analysis"] = (
        f"There were {guest_vs_registered['registered']} registered customers and {guest_vs_registered['guest']} guests. "
        f"Top customers by revenue are: {', '.join(f'{email} (${amount:,.2f})' for email, amount in top_customers)}. "
        f"Most customers are located in billing countries like {', '.join(billing_countries.keys())} and shipping countries like "
        f"{', '.join(shipping_countries.keys())}."
    )

    top_skus = sorted(product_qty.items(), key=lambda x: x[1], reverse=True)[:3]

    margin_samples = [
        round(p - c, 2) for c, p in cost_vs_price if c is not None and p is not None
    ]

    if margin_samples:
        avg_margin = mean(margin_samples)
    else:
        avg_margin = 0.0  # or some default value

    insights["3. Product & Inventory Insights"] = (
        f"Best-selling products are: {', '.join(f'{sku} (Qty: {qty})' for sku, qty in top_skus)}. "
        f"Average product margins are around ${avg_margin:,.2f} per item. "
        f"Pricing trends vary across SKUs, with {sum(len(v) for v in product_price_list.values())} price samples collected."
    )

    insights["4. Order Status and Processing"] = (
        f"{len(order_status_stuck)} orders appear stuck in 'pending' or 'processing'. "
        f"Average time to process/ship an order is {mean(processing_times)/3600:.2f} hours. "
        f"{refunded_orders} orders had refunds, and {cancelled_orders} orders were cancelled."
    )

    insights["5. Shipping and Fulfillment"] = (
        f"{free_shipping_count} orders qualified for free shipping. "
        f"Top shipping destinations include: {', '.join(list(shipping_destinations.keys())[:3])}. "
        f"Most frequently used shipping methods are: {', '.join(f'{k} ({v})' for k, v in shipping_methods.items())}."
    )

    # 6. Time-based breakdown
    now = datetime.utcnow()
    timeframes = {
        "Last 1 hour": now - timedelta(hours=1),
        "Today": datetime(now.year, now.month, now.day),
        "Yesterday": datetime(now.year, now.month, now.day) - timedelta(days=1),
        "Last 7 days": now - timedelta(days=7),
        "Last 10 days": now - timedelta(days=10),
        "Last 15 days": now - timedelta(days=15),
        "Last 30 days": now - timedelta(days=30),
        "Last 90 days": now - timedelta(days=90),
        "Last 180 days": now - timedelta(days=180),
        "Last 365 days": now - timedelta(days=365),
        "All time": datetime.min,
    }

    time_summary = []
    for label, start_time in timeframes.items():
        order_count = 0
        total_revenue = 0
        for order in orders:
            created_at_str = order.get("created_at", "")
            if not created_at_str:
                continue
            created_at = datetime.fromisoformat(created_at_str.replace("Z", "+00:00"))
            if created_at >= start_time:
                order_count += 1
                total_revenue += order.get("base_grand_total", 0)
        time_summary.append(
            f"{label}: {order_count} orders totaling ${total_revenue:,.2f}"
        )

    insights["6. Time-based Order and Revenue Breakdown"] = (
        "Here's how orders and revenue break down by time:\n" + "\n".join(time_summary)
    )

    return insights


def generate_product_insights(products: list, total_count: int) -> dict:
    if not products:
        return {
            "Product & Inventory Insights": "No product data available for insights."
        }

    total_products = total_count
    active_products = [
        p for p in products if p.get("status") == 1 or p.get("status") == 2
    ]
    active_count = len(active_products)

    prices = [
        p["price"] for p in active_products if isinstance(p.get("price"), (int, float))
    ]
    avg_price = round(mean(prices), 2) if prices else 0
    max_price_product = max(
        active_products, key=lambda x: x.get("price", 0), default={}
    )
    min_price_product = min(
        active_products, key=lambda x: x.get("price", 0), default={}
    )

    # Category analysis
    category_counter = Counter()
    for p in active_products:
        for attr in p.get("custom_attributes", []):
            if attr["attribute_code"] == "category_ids":
                category_counter.update(attr["value"])

    most_common_category = (
        category_counter.most_common(1)[0][0] if category_counter else "N/A"
    )

    # Product links
    upsell_links = sum(
        1
        for p in active_products
        for l in p.get("product_links", [])
        if l["link_type"] == "upsell"
    )
    related_links = sum(
        1
        for p in active_products
        for l in p.get("product_links", [])
        if l["link_type"] == "related"
    )
    avg_upsell_links = round(upsell_links / active_count, 2) if active_count else 0
    avg_related_links = round(related_links / active_count, 2) if active_count else 0

    # Image availability
    products_with_images = sum(
        1 for p in active_products if p.get("media_gallery_entries")
    )
    image_availability = (
        round((products_with_images / active_count) * 100, 2) if active_count else 0
    )

    # Manufacturers or suppliers
    supplier_counter = Counter()
    for p in active_products:
        for attr in p.get("custom_attributes", []):
            if attr["attribute_code"] in ["supplier", "manufacturer"]:
                supplier_counter.update([attr["value"]])
    top_supplier = (
        supplier_counter.most_common(1)[0][0] if supplier_counter else "Unknown"
    )

    dge_client = DGEClient()
    total_dge_products = dge_client.get_total_product_count()

    summary = (
        f"There are {active_count} active products listed in the store out of a total of {total_products}. (web shop) "
        f"Total products in DGE: {total_dge_products}. "
        f"The average price of an active product is {avg_price} euros. "
        f"The most expensive product is '{max_price_product.get('name', 'N/A')}' at {max_price_product.get('price', 'N/A')} euros, "
        f"while the cheapest is '{min_price_product.get('name', 'N/A')}' at {min_price_product.get('price', 'N/A')} euros. "
        f"The most frequently used product category ID is {most_common_category}. "
        f"Each product has an average of {avg_related_links} related links and {avg_upsell_links} upsell links, indicating robust cross-sell strategies. "
        f"Approximately {image_availability}% of products have at least one associated image. "
        f"The most frequently appearing supplier or manufacturer is ID '{top_supplier}'."
    )

    return {"Product & Inventory Insights": summary}


def generate_customer_insights(customers: list) -> dict:
    if not customers:
        return {"Customer Analysis": "No customer data available for insights."}

    total_customers = len(customers)
    active_customers = [c for c in customers if c.get("group_id") != 0]
    active_count = len(active_customers)

    # Email domain distribution
    email_domains = [
        c["email"].split("@")[-1] for c in active_customers if "email" in c
    ]
    top_email_domain = (
        Counter(email_domains).most_common(1)[0][0] if email_domains else "N/A"
    )

    # Created date distribution
    account_years = []
    for c in active_customers:
        created_at = c.get("created_at")
        try:
            year = datetime.fromisoformat(created_at).year
            account_years.append(year)
        except:
            continue
    most_common_year = (
        Counter(account_years).most_common(1)[0][0] if account_years else "N/A"
    )

    # Region/country breakdown
    region_counter = Counter()
    country_counter = Counter()
    for c in active_customers:
        addresses = c.get("addresses", [])
        for addr in addresses:
            region = addr.get("region", {}).get("region", None)
            country = addr.get("country_id")
            if region:
                region_counter.update([region])
            if country:
                country_counter.update([country])

    top_region = region_counter.most_common(1)[0][0] if region_counter else "N/A"
    top_country = country_counter.most_common(1)[0][0] if country_counter else "N/A"

    # Customer group distribution
    group_counter = Counter(
        [c["group_id"] for c in active_customers if "group_id" in c]
    )
    top_group_id = group_counter.most_common(1)[0][0] if group_counter else "N/A"

    # Default billing & shipping address presence
    billing_present = sum(1 for c in active_customers if c.get("default_billing"))
    shipping_present = sum(1 for c in active_customers if c.get("default_shipping"))
    billing_pct = (
        round((billing_present / active_count) * 100, 2) if active_count else 0
    )
    shipping_pct = (
        round((shipping_present / active_count) * 100, 2) if active_count else 0
    )

    summary = (
        f"There are {active_count} active customers out of a total of {total_customers}. "
        f"The most common email domain among customers is '{top_email_domain}', indicating popular usage patterns. "
        f"The majority of customer accounts were created in the year {most_common_year}. "
        f"Geographically, most customers are located in the region '{top_region}' and the country '{top_country}'. "
        f"The most common customer group ID is '{top_group_id}', which may reflect specific pricing or access tiers. "
        f"Approximately {billing_pct}% of customers have a default billing address set, while {shipping_pct}% have a default shipping address configured."
    )

    return {"Customer Analysis": summary}
