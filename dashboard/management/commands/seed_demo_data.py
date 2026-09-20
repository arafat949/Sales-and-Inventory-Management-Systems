import random
from datetime import timedelta
from decimal import Decimal

from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone

from accounts.models import User
from customers.models import Customer
from expenses.models import Expense
from inventory.models import InventoryTransaction
from products.models import Category, Product
from purchases.models import Purchase, PurchaseItem
from sales.models import Sale, SaleItem
from suppliers.models import Supplier

CATEGORY_NAMES = ['Beverages', 'Snacks', 'Dairy', 'Personal Care', 'Stationery', 'Electronics Accessories']

PRODUCTS = [
    ('Mineral Water 1L', 'Beverages', 20, 35, 8, 15),
    ('Cola Can 330ml', 'Beverages', 25, 45, 5, 20),
    ('Potato Chips 150g', 'Snacks', 40, 65, 3, 12),
    ('Chocolate Bar 45g', 'Snacks', 30, 50, 2, 25),
    ('Milk 1L', 'Dairy', 60, 85, 20, 10),
    ('Butter 200g', 'Dairy', 150, 210, 3, 8),
    ('Toothpaste 100g', 'Personal Care', 80, 130, 40, 15),
    ('Shampoo 200ml', 'Personal Care', 180, 260, 3, 10),
    ('Ballpoint Pen (Box of 10)', 'Stationery', 90, 140, 2, 20),
    ('Notebook A4', 'Stationery', 45, 75, 60, 30),
    ('USB Cable Type-C', 'Electronics Accessories', 120, 220, 1, 10),
    ('Phone Case (Universal)', 'Electronics Accessories', 90, 180, 2, 10),
]

CUSTOMER_NAMES = [
    ('Rahim Uddin', 'REGULAR'), ('Karim Hossain', 'VIP'), ('Fatema Begum', 'NEW'),
    ('Nasrin Akter', 'REGULAR'), ('Shafiq Islam', 'VIP'), ('Jannatul Ferdous', 'NEW'),
]

SUPPLIER_NAMES = [
    'Dhaka Wholesale Traders', 'Chattogram Distribution Co.', 'Northern Supply House',
]

EXPENSE_SAMPLES = [
    ('Shop Rent - Monthly', 'RENT', 25000),
    ('Staff Salary', 'SALARY', 40000),
    ('Electricity Bill', 'ELECTRICITY', 4500),
    ('Delivery Van Fuel', 'TRANSPORTATION', 3000),
    ('Facebook Ads', 'MARKETING', 5000),
    ('Shelf Repair', 'MAINTENANCE', 2200),
]


class Command(BaseCommand):
    help = 'Seeds the database with realistic demo data (categories, products, customers, suppliers, purchases, sales, expenses).'

    def add_arguments(self, parser):
        parser.add_argument('--months', type=int, default=6, help='How many months of sales history to generate.')

    @transaction.atomic
    def handle(self, *args, **options):
        months = options['months']
        admin_user = User.objects.filter(role='ADMIN').first()
        if not admin_user:
            self.stdout.write(self.style.ERROR('No ADMIN user found. Create one first with createsuperuser.'))
            return

        self.stdout.write('Seeding categories...')
        categories = {}
        for name in CATEGORY_NAMES:
            cat, _ = Category.objects.get_or_create(name=name)
            categories[name] = cat

        self.stdout.write('Seeding suppliers...')
        suppliers = []
        for i, name in enumerate(SUPPLIER_NAMES, start=1):
            sup, _ = Supplier.objects.get_or_create(
                company_name=name,
                defaults={'contact_person': f'Contact Person {i}', 'phone': f'017{i}0000000', 'email': f'supplier{i}@example.com'}
            )
            suppliers.append(sup)

        self.stdout.write('Seeding customers...')
        customers = []
        for i, (name, ctype) in enumerate(CUSTOMER_NAMES, start=1):
            cust, _ = Customer.objects.get_or_create(
                name=name,
                defaults={'phone': f'018{i}1111111', 'email': f'customer{i}@example.com', 'customer_type': ctype}
            )
            customers.append(cust)

        self.stdout.write('Seeding products...')
        products = []
        for name, cat_name, purchase_price, selling_price, stock, min_stock in PRODUCTS:
            prod, created = Product.objects.get_or_create(
                name=name,
                defaults={
                    'sku': f"SKU-{random.randint(10000, 99999)}",
                    'category': categories[cat_name],
                    'supplier': random.choice(suppliers),
                    'purchase_price': Decimal(purchase_price),
                    'selling_price': Decimal(selling_price),
                    'current_stock': stock,
                    'minimum_stock': min_stock,
                }
            )
            products.append(prod)

        self.stdout.write(f'Seeding {months} months of sales history...')
        today = timezone.localdate()
        start_day = today - timedelta(days=months * 30)
        day = start_day
        sale_count = 0
        while day <= today:
            num_sales_today = random.randint(0, 4)
            for _ in range(num_sales_today):
                customer = random.choice(customers) if random.random() > 0.2 else None
                sale = Sale.objects.create(
                    customer=customer,
                    created_by=admin_user,
                    payment_method=random.choice(['CASH', 'CARD', 'MOBILE_BANKING']),
                    payment_status='PAID',
                    status='COMPLETED',
                )
                # backdate sale_date (auto_now_add, so update directly after creation)
                fake_datetime = timezone.make_aware(
                    timezone.datetime.combine(day, timezone.datetime.min.time()) + timedelta(hours=random.randint(9, 20))
                )
                Sale.objects.filter(pk=sale.pk).update(sale_date=fake_datetime, created_at=fake_datetime)

                num_items = random.randint(1, 3)
                chosen_products = random.sample(products, num_items)
                for prod in chosen_products:
                    qty = random.randint(1, 5)
                    SaleItem.objects.create(sale=sale, product=prod, quantity=qty, unit_price=prod.selling_price)
                sale.refresh_from_db()
                sale.recalculate_totals()
                sale_count += 1
            day += timedelta(days=1)

        self.stdout.write('Seeding a few purchases...')
        for i in range(6):
            purchase_day = today - timedelta(days=random.randint(1, months * 30))
            purchase = Purchase.objects.create(
                supplier=random.choice(suppliers),
                created_by=admin_user,
                purchase_date=purchase_day,
                payment_status=random.choice(['PAID', 'PARTIAL']),
                status='COMPLETED',
            )
            for prod in random.sample(products, 3):
                qty = random.randint(20, 60)
                PurchaseItem.objects.create(purchase=purchase, product=prod, quantity=qty, unit_cost=prod.purchase_price)
            purchase.recalculate_total()

        self.stdout.write('Seeding expenses...')
        for title, cat, amount in EXPENSE_SAMPLES:
            for m in range(months):
                exp_date = today - timedelta(days=m * 30 + random.randint(0, 5))
                Expense.objects.get_or_create(
                    title=title, expense_date=exp_date,
                    defaults={'category': cat, 'amount': Decimal(amount), 'created_by': admin_user}
                )

        self.stdout.write(self.style.SUCCESS(
            f'Done. Created/updated {len(products)} products, {len(customers)} customers, '
            f'{len(suppliers)} suppliers, {sale_count} sales, plus purchases and expenses.'
        ))
