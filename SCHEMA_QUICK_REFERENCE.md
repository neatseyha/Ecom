# QUICK REFERENCE: MISSING FIELDS BY PRIORITY

## 🔴 CRITICAL - Add These Immediately

### PRODUCT Table - Add 5 Fields
```
✓ sku (String)           - Product unique code
✓ color (String)         - Product color variant  
✓ size (String)          - Product size variant
✓ brand (String)         - Product brand
✓ discount_percentage (Float) - Sale discount %
```

### USER Table - Add 8 Fields
```
✓ first_name (String)    - Customer first name
✓ last_name (String)     - Customer last name
✓ phone (String)         - Contact phone
✓ address (String)       - Street address
✓ city (String)          - City
✓ state (String)         - State/Province
✓ zip_code (String)      - Postal code
✓ country (String)       - Country
```

### ORDER Table - Add 6 Fields + FIX STRUCTURE
```
✓ order_number (String)      - Unique order ID (e.g., ORD-20260415-001)
✓ payment_method (String)    - How paid (card, cash, bank transfer)
✓ payment_status (String)    - Payment status (pending, paid, failed)
✓ discount_amount (Float)    - Total discount
✓ shipping_cost (Float)      - Shipping fee
✓ tax_amount (Float)         - Tax amount
✓ grand_total (Float)        - Final total
❌ FIX: product_id is WRONG - one order needs MULTIPLE items
   → Create OrderItem table instead
```

### CREATE 4 New Tables (CRITICAL!)
```
1️⃣  CartItem       - Shopping cart (doesn't exist yet!)
2️⃣  OrderItem      - Multiple items per order
3️⃣  Payment        - Track payments
4️⃣  Address        - Customer addresses
```

---

## 🟡 MEDIUM - Add When Convenient

### PRODUCT Table - Add 7 Fields
```
• image_medium (String)    - 400x400 image
• image_small (String)     - 200x200 image  
• discount_price (Float)   - Discounted price
• rating_avg (Float)       - Average rating (cached)
• review_count (Integer)   - Total reviews
• is_featured (Boolean)    - Featured on homepage
• weight (Float)           - For shipping
```

### CATEGORY Table - Add 6 Fields
```
• parent_id (FK)        - For subcategories
• slug (String)         - URL friendly name
• icon (String)         - Icon/image
• image (String)        - Category banner
• display_order (Int)   - Sort order
• status (String)       - Active/Inactive
```

### RATING Table - Add 5 Fields
```
• review_title (String)      - Review headline
• helpful_yes_count (Int)    - Helpful votes
• helpful_no_count (Int)     - Not helpful votes
• images (String)            - Review photos
• status (String)            - Moderation status
```

### WISHLIST Table - Add 3 Fields
```
• priority (String)      - high/medium/low
• category_type (String) - favorites/watch-later/gifts
• target_price (Float)   - Price alert threshold
```

### CREATE 3 New Tables
```
1️⃣  Shipping       - Shipping tracking
2️⃣  Coupon         - Promotional codes
3️⃣  Brand          - Brand management
```

---

## 🟢 LOW - Add for Polish

### PRODUCT Table - Add 4 Fields
```
◇ dimensions (String)     - Product size
◇ meta_description (String) - SEO
◇ meta_keywords (String)  - SEO
◇ view_count (Integer)    - Popularity tracker
```

### USER Table - Add 6 Fields
```
◇ profile_picture (String) - Avatar
◇ gender (String)          - M/F/Other
◇ date_of_birth (Date)     - DOB
◇ bio (String)             - Bio/intro
◇ email_verified (Bool)    - Email confirmed
◇ newsletter_subscribed (Bool) - Newsletter opt-in
```

---

## FIELD COUNT SUMMARY

| Table | Current | Missing | After Fix |
|-------|---------|---------|-----------|
| **Product** | 10 | 17 | 27 |
| **User** | 7 | 18 | 25 |
| **Order** | 13 | 17 | 30 |
| **Category** | 3 | 9 | 12 |
| **Rating** | 8 | 8 | 16 |
| **Wishlist** | 7 | 5 | 12 |
| **CartItem** | ❌ | 8 | 8 |
| **OrderItem** | ❌ | 8 | 8 |
| **Payment** | ❌ | 9 | 9 |
| **Address** | ❌ | 9 | 9 |
| **Shipping** | ❌ | 7 | 7 |
| **Coupon** | ❌ | 11 | 11 |
| **Brand** | ❌ | 7 | 7 |
| | | | **181 total** |

---

## IMPLEMENTATION CHECKLIST

### Phase 1: Core Fields (1-2 days)
- [ ] Add color, size, sku, brand to Product
- [ ] Add first_name, last_name, phone, addresses to User
- [ ] Add payment fields to Order
- [ ] Create CartItem table
- [ ] Create OrderItem table
- [ ] Refactor Order to use OrderItem

### Phase 2: Payment & Shipping (1-2 days)
- [ ] Create Payment table
- [ ] Create Address table
- [ ] Create Shipping table
- [ ] Update Order relationships

### Phase 3: Features (1 day)
- [ ] Create Coupon table
- [ ] Create Brand table
- [ ] Add review_title, helpful voting to Rating
- [ ] Add parent_id, slug to Category

### Phase 4: Polish (1 day)
- [ ] Add optional fields (weight, dimensions, etc.)
- [ ] Add SEO fields (meta_description, keywords)
- [ ] Create database indices
- [ ] Test all relationships

---

## DATA RELATIONSHIPS (After Fix)

```
User
├── Orders (1:Many)
├── Wishlists (1:Many)
├── Ratings (1:Many)
├── CartItems (1:Many)
├── Addresses (1:Many)
└── Orders → OrderItems (1:Many per Order)
                        └── Product (Many:1)

Product
├── Category (Many:1)
├── Brand (Many:1)
├── OrderItems (1:Many)
├── CartItems (1:Many)
├── Ratings (1:Many)
├── Wishlists (1:Many)
└── Images (thumbnail, medium, original)

Order
├── User (Many:1)
├── OrderItems (1:Many)
├── Payment (1:1)
├── Shipping (1:1)
└── Addresses (for billing & shipping)
```

---

## BEFORE & AFTER EXAMPLE: Product Order Flow

### ❌ CURRENT (BROKEN)
```
Order Table (Single Product Only):
- id: 1
- user_id: 5
- product_id: 10        ← ONE PRODUCT ONLY!
- quantity: 2
- price: $50
- total_price: $100

Problem: Can't order 2+ different products!
```

### ✅ RECOMMENDED (CORRECT)
```
Order Table (Multiple Products):
- id: 1
- order_number: "ORD-20260415-001"
- user_id: 5
- subtotal: $250
- discount_amount: $25
- tax_amount: $18.75
- shipping_cost: $10
- grand_total: $253.75
- payment_method: "credit_card"
- payment_status: "paid"
- status: "shipped"
- created_at: 2026-04-15

OrderItem Table (Multiple Rows):
┌─────────────────────────────────────┐
│ OrderItem 1                         │
│ - order_id: 1                      │
│ - product_id: 10 (Red Shirt, S)    │
│ - quantity: 2                      │
│ - unit_price: $50                  │
│ - total: $100                      │
└─────────────────────────────────────┘
┌─────────────────────────────────────┐
│ OrderItem 2                         │
│ - order_id: 1                      │
│ - product_id: 20 (Blue Pants, M)   │
│ - quantity: 1                      │
│ - unit_price: $150                 │
│ - total: $150                      │
└─────────────────────────────────────┘

Payment Table:
- order_id: 1
- amount: $253.75
- payment_method: "credit_card"
- transaction_id: "txn_abc123xyz"
- status: "completed"

Shipping Table:
- order_id: 1
- tracking_number: "FX123456789"
- carrier: "FedEx"
- status: "in_transit"
- estimated_delivery: 2026-04-20

✓ Now supports multiple products per order!
```

---

## FORM UPDATES NEEDED

### Add Product Form - Add Fields
```
Current Fields:
✓ Product Name
✓ Category
✓ Price
✓ Stock
✓ Description
✓ Image

NEW FIELDS TO ADD:
→ SKU
→ Brand (dropdown)
→ Color (text or multi-select)
→ Size (S, M, L, XL, etc.)
→ Discount % (for sales)
→ Weight (for shipping)
```

### User Registration/Profile - Add Fields
```
Current Fields:
✓ Username
✓ Email
✓ Password

NEW FIELDS TO ADD:
→ First Name
→ Last Name
→ Phone Number
→ Address
→ City
→ State
→ Zip Code
→ Country
→ Gender (optional)
→ Date of Birth (optional)
```

### Order Management - New Fields
```
Current:
✓ Customer Name
✓ Email
✓ Phone
✓ Shipping Address
✓ Status

NEW FIELDS:
→ Order Number (auto-generated)
→ Payment Method
→ Payment Status
→ Discount Amount
→ Tax Amount
→ Shipping Cost
→ Grand Total
→ Tracking Number (after shipping)
```

---

## TABLE STRUCTURE QUICK VIEW

```
✅ KEEP (Already Good)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Product: base structure solid
User: authentication working
Category: basic structure OK
Rating: reviews working
Wishlist: core logic fine

⚠️  MODIFY (Add Missing Fields)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Product → Add: sku, color, size, brand, discount fields
User → Add: name, phone, address fields
Order → Add: payment, discount, tax fields (MAJOR)
Category → Add: hierarchy, slug, status
Rating → Add: title, voting system
Wishlist → Add: priority, categories

❌ CREATE NEW (Missing Tables)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
CartItem → Shopping cart
OrderItem → Multiple products per order
Payment → Payment tracking
Address → Multiple addresses
Shipping → Shipping tracking
Coupon → Promo codes
Brand → Brand management
```

---

## ESTIMATED SQL MIGRATION

```sql
-- Phase 1: Product updates
ALTER TABLE product ADD COLUMN sku VARCHAR(50) UNIQUE;
ALTER TABLE product ADD COLUMN color VARCHAR(100);
ALTER TABLE product ADD COLUMN size VARCHAR(100);
ALTER TABLE product ADD COLUMN brand VARCHAR(80);
ALTER TABLE product ADD COLUMN discount_percentage FLOAT DEFAULT 0;
ALTER TABLE product ADD COLUMN discount_price FLOAT;
ALTER TABLE product ADD COLUMN image_medium VARCHAR(120);
ALTER TABLE product ADD COLUMN image_small VARCHAR(120);
ALTER TABLE product ADD COLUMN rating_avg FLOAT DEFAULT 0;
ALTER TABLE product ADD COLUMN review_count INTEGER DEFAULT 0;

-- Phase 1: User updates
ALTER TABLE user ADD COLUMN first_name VARCHAR(50);
ALTER TABLE user ADD COLUMN last_name VARCHAR(50);
ALTER TABLE user ADD COLUMN phone VARCHAR(20);
ALTER TABLE user ADD COLUMN address VARCHAR(255);
ALTER TABLE user ADD COLUMN city VARCHAR(50);
ALTER TABLE user ADD COLUMN state VARCHAR(50);
ALTER TABLE user ADD COLUMN zip_code VARCHAR(20);
ALTER TABLE user ADD COLUMN country VARCHAR(50);

-- Phase 1: Order updates (CRITICAL)
ALTER TABLE order ADD COLUMN order_number VARCHAR(20) UNIQUE;
ALTER TABLE order ADD COLUMN payment_method VARCHAR(50);
ALTER TABLE order ADD COLUMN payment_status VARCHAR(50);
ALTER TABLE order ADD COLUMN discount_amount FLOAT DEFAULT 0;
ALTER TABLE order ADD COLUMN shipping_cost FLOAT DEFAULT 0;
ALTER TABLE order ADD COLUMN tax_amount FLOAT DEFAULT 0;
ALTER TABLE order ADD COLUMN grand_total FLOAT;

-- Phase 1: Create OrderItem table (CRITICAL)
CREATE TABLE order_item (
    id INTEGER PRIMARY KEY,
    order_id INTEGER NOT NULL,
    product_id INTEGER NOT NULL,
    product_name VARCHAR(255),
    quantity INTEGER,
    unit_price FLOAT,
    discount FLOAT DEFAULT 0,
    total FLOAT,
    size VARCHAR(50),
    color VARCHAR(100),
    FOREIGN KEY(order_id) REFERENCES order(id),
    FOREIGN KEY(product_id) REFERENCES product(id)
);

-- Phase 1: Create CartItem table (CRITICAL)
CREATE TABLE cart_item (
    id INTEGER PRIMARY KEY,
    user_id INTEGER NOT NULL,
    product_id INTEGER NOT NULL,
    quantity INTEGER DEFAULT 1,
    price FLOAT,
    size VARCHAR(50),
    color VARCHAR(100),
    added_date DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(user_id) REFERENCES user(id),
    FOREIGN KEY(product_id) REFERENCES product(id)
);

-- Continue with remaining phases...
```

