PRODUCTS = [
    {'name': 'Laptop Pro 15"', 'price': 1299.00, 'cost': 850.00},
    {'name': 'Wireless Monitor 27"', 'price': 449.00, 'cost': 280.00},
    {'name': 'Mechanical Keyboard', 'price': 129.00, 'cost': 65.00},
    {'name': 'Ergonomic Mouse', 'price': 79.00, 'cost': 35.00},
    {'name': 'Noise-Cancelling Headphones', 'price': 349.00, 'cost': 180.00},
    {'name': 'HD Webcam', 'price': 99.00, 'cost': 45.00},
    {'name': 'USB-C Hub', 'price': 69.00, 'cost': 28.00},
    {'name': 'Phone Case', 'price': 29.00, 'cost': 8.00},
    {'name': 'Standing Desk', 'price': 599.00, 'cost': 320.00},
    {'name': 'Office Chair', 'price': 449.00, 'cost': 220.00},
    {'name': 'Bookshelf', 'price': 189.00, 'cost': 95.00},
    {'name': 'Filing Cabinet', 'price': 159.00, 'cost': 80.00},
    {'name': 'Whiteboard 48x36', 'price': 89.00, 'cost': 40.00},
    {'name': 'Desk Lamp', 'price': 59.00, 'cost': 22.00},
    {'name': 'T-Shirt (Branded)', 'price': 24.99, 'cost': 8.00},
    {'name': 'Hoodie (Branded)', 'price': 54.99, 'cost': 22.00},
    {'name': 'Baseball Cap', 'price': 19.99, 'cost': 6.00},
    {'name': 'Backpack', 'price': 79.00, 'cost': 32.00},
    {'name': 'Water Bottle', 'price': 14.99, 'cost': 4.00},
    {'name': 'Coffee Mug', 'price': 12.99, 'cost': 3.50},
    {'name': 'Notebook (Premium)', 'price': 18.00, 'cost': 5.00},
    {'name': 'Pen Set', 'price': 24.00, 'cost': 8.00},
    {'name': 'Paper Ream (500 sheets)', 'price': 9.99, 'cost': 4.50},
    {'name': 'Wireless Charger', 'price': 39.00, 'cost': 15.00},
    {'name': 'Portable Speaker', 'price': 59.00, 'cost': 25.00},
]

RAW_MATERIALS = [
    {'name': 'Steel Sheet (4x8)', 'price': 85.00, 'cost': 55.00},
    {'name': 'Aluminum Rod (6ft)', 'price': 42.00, 'cost': 28.00},
    {'name': 'Copper Wire (100ft)', 'price': 65.00, 'cost': 45.00},
    {'name': 'Plastic Pellets (25lb)', 'price': 38.00, 'cost': 22.00},
    {'name': 'Wood Panel (Birch)', 'price': 55.00, 'cost': 32.00},
    {'name': 'Glass Pane (24x36)', 'price': 48.00, 'cost': 30.00},
    {'name': 'Rubber Strip (10ft)', 'price': 18.00, 'cost': 10.00},
    {'name': 'Fabric Roll (Cotton)', 'price': 75.00, 'cost': 45.00},
    {'name': 'Circuit Board (PCB)', 'price': 12.00, 'cost': 6.00},
    {'name': 'LED Module', 'price': 8.00, 'cost': 3.50},
    {'name': 'Battery Cell (Li-ion)', 'price': 15.00, 'cost': 9.00},
    {'name': 'Motor Unit (DC)', 'price': 28.00, 'cost': 16.00},
    {'name': 'Screw Pack (100pc)', 'price': 6.00, 'cost': 2.50},
    {'name': 'Bolt Set (50pc)', 'price': 9.00, 'cost': 4.00},
    {'name': 'Adhesive (Industrial)', 'price': 14.00, 'cost': 7.00},
]

SERVICES = [
    {'name': 'Consulting (1hr)', 'price': 150.00, 'cost': 0},
    {'name': 'Training Session', 'price': 500.00, 'cost': 0},
    {'name': 'Support Ticket', 'price': 75.00, 'cost': 0},
    {'name': 'Design Service', 'price': 200.00, 'cost': 0},
    {'name': 'Installation Service', 'price': 250.00, 'cost': 0},
]

WORK_CENTERS = [
    {'name': 'Assembly Line A', 'capacity': 5, 'cost': 35.00},
    {'name': 'Assembly Line B', 'capacity': 3, 'cost': 35.00},
    {'name': 'Quality Control', 'capacity': 2, 'cost': 25.00},
    {'name': 'Packaging Station', 'capacity': 4, 'cost': 20.00},
    {'name': 'Welding Shop', 'capacity': 2, 'cost': 45.00},
    {'name': 'Paint Booth', 'capacity': 1, 'cost': 40.00},
    {'name': 'CNC Machine', 'capacity': 1, 'cost': 60.00},
    {'name': 'Testing Lab', 'capacity': 3, 'cost': 30.00},
]

# Finished goods → components (indices into RAW_MATERIALS)
BOM_TEMPLATES = [
    {
        'product': 'Laptop Pro 15"',
        'components': [
            ('Circuit Board (PCB)', 2),
            ('Battery Cell (Li-ion)', 4),
            ('LED Module', 1),
            ('Plastic Pellets (25lb)', 0.5),
            ('Screw Pack (100pc)', 0.2),
        ]
    },
    {
        'product': 'Standing Desk',
        'components': [
            ('Wood Panel (Birch)', 3),
            ('Steel Sheet (4x8)', 1),
            ('Screw Pack (100pc)', 0.5),
            ('Bolt Set (50pc)', 0.3),
        ]
    },
    {
        'product': 'Office Chair',
        'components': [
            ('Steel Sheet (4x8)', 0.5),
            ('Fabric Roll (Cotton)', 2),
            ('Rubber Strip (10ft)', 1),
            ('Screw Pack (100pc)', 0.3),
            ('Bolt Set (50pc)', 0.2),
        ]
    },
    {
        'product': 'Wireless Monitor 27"',
        'components': [
            ('Circuit Board (PCB)', 1),
            ('Glass Pane (24x36)', 1),
            ('LED Module', 3),
            ('Plastic Pellets (25lb)', 0.3),
        ]
    },
    {
        'product': 'Portable Speaker',
        'components': [
            ('Circuit Board (PCB)', 1),
            ('Battery Cell (Li-ion)', 2),
            ('Plastic Pellets (25lb)', 0.2),
            ('Motor Unit (DC)', 1),
        ]
    },
]

PROJECTS = [
    'Website Redesign',
    'Mobile App Development',
    'ERP Implementation',
    'Office Renovation',
    'Q1 Marketing Campaign',
    'Product Launch - v2.0',
    'Data Migration',
    'Security Audit',
    'Process Optimization',
    'Customer Portal',
    'Warehouse Automation',
    'Brand Refresh',
    'API Integration',
    'Employee Onboarding System',
    'Annual Report',
]

TASK_NAMES = [
    'Requirements gathering',
    'Design mockups',
    'Backend development',
    'Frontend development',
    'Database schema',
    'API endpoints',
    'Unit testing',
    'Integration testing',
    'User acceptance testing',
    'Documentation',
    'Deployment',
    'Code review',
    'Performance optimization',
    'Security review',
    'Stakeholder demo',
    'Bug fixes',
    'Data migration scripts',
    'Training materials',
    'Go-live preparation',
    'Post-launch monitoring',
]

TIMESHEET_DESCRIPTIONS = [
    'Sprint planning and backlog grooming',
    'Code review and feedback',
    'Bug investigation and fix',
    'Feature development',
    'Client meeting',
    'Technical documentation',
    'Database optimization',
    'UI/UX improvements',
    'Testing and QA',
    'Deployment and monitoring',
    'Research and prototyping',
    'Team standup and sync',
]

EXPENSE_ITEMS = [
    {'name': 'Flight - Client Visit', 'amount': 450.00},
    {'name': 'Hotel (2 nights)', 'amount': 320.00},
    {'name': 'Client Dinner', 'amount': 125.00},
    {'name': 'Uber/Taxi', 'amount': 45.00},
    {'name': 'Office Supplies', 'amount': 85.00},
    {'name': 'Software License', 'amount': 199.00},
    {'name': 'Conference Ticket', 'amount': 599.00},
    {'name': 'Team Lunch', 'amount': 180.00},
    {'name': 'Parking (monthly)', 'amount': 150.00},
    {'name': 'Fuel Reimbursement', 'amount': 65.00},
    {'name': 'Internet (home office)', 'amount': 79.00},
    {'name': 'Phone Bill', 'amount': 55.00},
    {'name': 'Training Course', 'amount': 299.00},
    {'name': 'Books & Materials', 'amount': 45.00},
    {'name': 'Co-working Space', 'amount': 250.00},
]

JOB_TITLES = [
    'Software Engineer',
    'Project Manager',
    'Sales Representative',
    'Marketing Coordinator',
    'Accountant',
    'HR Specialist',
    'Warehouse Manager',
    'Quality Engineer',
    'Product Designer',
    'Operations Manager',
    'Customer Support Lead',
    'Data Analyst',
    'DevOps Engineer',
    'Business Analyst',
    'Office Administrator',
]

DEPARTMENTS = [
    'Engineering',
    'Sales',
    'Marketing',
    'Finance',
    'Human Resources',
    'Operations',
    'Quality Assurance',
    'Customer Support',
    'Design',
    'Management',
]

VEHICLE_BRANDS_MODELS = [
    ('Toyota', 'Camry'),
    ('Toyota', 'RAV4'),
    ('Honda', 'Civic'),
    ('Honda', 'CR-V'),
    ('Ford', 'F-150'),
    ('Ford', 'Explorer'),
    ('Tesla', 'Model 3'),
    ('Tesla', 'Model Y'),
    ('BMW', 'X3'),
    ('BMW', '3 Series'),
    ('Chevrolet', 'Silverado'),
    ('Chevrolet', 'Equinox'),
    ('Hyundai', 'Tucson'),
    ('Nissan', 'Altima'),
    ('Subaru', 'Outback'),
]

CRM_NAMES = [
    'New ERP implementation',
    'Office furniture order',
    'IT infrastructure upgrade',
    'Annual supply contract',
    'Website development project',
    'Consulting engagement',
    'Training program',
    'Software licensing deal',
    'Hardware refresh',
    'Managed services contract',
    'Cloud migration project',
    'Security assessment',
    'Data analytics platform',
    'Mobile app development',
    'Digital transformation',
    'Custom integration',
    'Support contract renewal',
    'Expansion project',
    'Process automation',
    'Compliance audit services',
]

OPERATION_NAMES = [
    'Cut to size',
    'Assemble frame',
    'Solder components',
    'Apply coating',
    'Quality inspection',
    'Final assembly',
    'Packaging',
    'Burn-in test',
    'Calibration',
    'Surface finishing',
]

JOURNAL_ENTRY_TEMPLATES = [
    # Expense entries (debit expense account, credit bank)
    {'description': 'Monthly Rent Payment', 'account_code': '612000', 'account_type': 'expense', 'entry_type': 'expense', 'min_amount': 3000, 'max_amount': 8000},
    {'description': 'R&D Project Costs', 'account_code': '961000', 'account_type': 'expense', 'entry_type': 'expense', 'min_amount': 8000, 'max_amount': 45000},
    {'description': 'Sales & Marketing Campaign', 'account_code': '962000', 'account_type': 'expense', 'entry_type': 'expense', 'min_amount': 3000, 'max_amount': 18000},
    {'description': 'Bank Service Charges', 'account_code': '620000', 'account_type': 'expense', 'entry_type': 'expense', 'min_amount': 50, 'max_amount': 450},
    {'description': 'Payroll - Monthly Salaries', 'account_code': '630000', 'account_type': 'expense', 'entry_type': 'expense', 'min_amount': 40000, 'max_amount': 120000},
    {'description': 'Office Equipment Purchase', 'account_code': '611000', 'account_type': 'expense', 'entry_type': 'expense', 'min_amount': 2000, 'max_amount': 25000},
    {'description': 'Utilities Payment', 'account_code': '612000', 'account_type': 'expense', 'entry_type': 'expense', 'min_amount': 800, 'max_amount': 3000},
    {'description': 'Professional Services', 'account_code': '600000', 'account_type': 'expense', 'entry_type': 'expense', 'min_amount': 2000, 'max_amount': 15000},
    # Liability entries (debit bank, credit liability)
    {'description': 'Deferred Revenue - Annual Contract', 'account_code': '212000', 'account_type': 'liability_current', 'entry_type': 'liability', 'min_amount': 5000, 'max_amount': 30000},
    {'description': 'Long-term Loan Proceeds', 'account_code': '291000', 'account_type': 'liability_non_current', 'entry_type': 'liability', 'min_amount': 25000, 'max_amount': 200000},
    {'description': 'Credit Card Statement', 'account_code': '201100', 'account_type': 'liability_current', 'entry_type': 'liability', 'min_amount': 500, 'max_amount': 5000},
    {'description': 'Salary Payable Accrual', 'account_code': '230000', 'account_type': 'liability_current', 'entry_type': 'liability', 'min_amount': 15000, 'max_amount': 60000},
    # Asset entries (debit asset, credit bank)
    {'description': 'Capital Investment', 'account_code': '101100', 'account_type': 'asset_current', 'entry_type': 'asset', 'min_amount': 50000, 'max_amount': 200000},
    {'description': 'Property Down Payment', 'account_code': '150000', 'account_type': 'asset_fixed', 'entry_type': 'asset', 'min_amount': 75000, 'max_amount': 350000},
    {'description': 'Computer Equipment', 'account_code': '160000', 'account_type': 'asset_non_current', 'entry_type': 'asset', 'min_amount': 3000, 'max_amount': 40000},
]

# -- Name / address pools (replace Faker) --

FIRST_NAMES = [
    'James', 'Mary', 'Robert', 'Patricia', 'John', 'Jennifer', 'Michael', 'Linda',
    'David', 'Elizabeth', 'William', 'Barbara', 'Richard', 'Susan', 'Joseph', 'Jessica',
    'Thomas', 'Sarah', 'Daniel', 'Karen', 'Aisha', 'Omar', 'Priya', 'Wei', 'Sofia',
    'Luca', 'Fatima', 'Hiroshi', 'Elena', 'Carlos',
]
LAST_NAMES = [
    'Smith', 'Johnson', 'Williams', 'Brown', 'Jones', 'Garcia', 'Miller', 'Davis',
    'Rodriguez', 'Martinez', 'Hernandez', 'Lopez', 'Wilson', 'Anderson', 'Thomas',
    'Taylor', 'Moore', 'Jackson', 'Martin', 'Lee', 'Khan', 'Patel', 'Nguyen', 'Kim',
    'Rossi', 'Silva', 'Novak', 'Tanaka', 'Ivanov', 'Okafor',
]
COMPANY_WORDS = [
    'Apex', 'Nova', 'Summit', 'Horizon', 'Vertex', 'Pioneer', 'Quantum', 'Atlas',
    'Beacon', 'Cascade', 'Zenith', 'Harbor', 'Orion', 'Sterling', 'Meridian',
]
COMPANY_SUFFIXES = [
    'Ltd', 'Inc', 'LLC', 'Group', 'Industries', 'Solutions', 'Technologies',
    'Logistics', 'Partners', 'Holdings',
]
STREET_NAMES = [
    'Main St', 'Oak Ave', 'Maple Dr', 'Cedar Ln', 'Park Blvd', 'Lake Rd', 'Hill St',
    'River Rd', 'Elm St', 'Pine Ave', 'Washington Ave', 'Sunset Blvd',
]
CITIES = [
    'Springfield', 'Riverside', 'Fairview', 'Madison', 'Georgetown', 'Clinton', 'Franklin',
    'Greenville', 'Bristol', 'Salem', 'Dover', 'Newport', 'Ashland', 'Burlington',
]
