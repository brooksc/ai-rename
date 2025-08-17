"""Sample documents and test data for ai-rename tests."""

# Sample PDF content (minimal PDF structure)
SAMPLE_PDF_CONTENT = b"""%PDF-1.4
1 0 obj
<<
/Type /Catalog
/Pages 2 0 R
>>
endobj

2 0 obj
<<
/Type /Pages
/Kids [3 0 R]
/Count 1
>>
endobj

3 0 obj
<<
/Type /Page
/Parent 2 0 R
/MediaBox [0 0 612 792]
/Contents 4 0 R
>>
endobj

4 0 obj
<<
/Length 44
>>
stream
BT
/F1 12 Tf
72 720 Td
(Sample PDF content) Tj
ET
endstream
endobj

xref
0 5
0000000000 65535 f 
0000000010 00000 n 
0000000056 00000 n 
0000000111 00000 n 
0000000180 00000 n 
trailer
<<
/Size 5
/Root 1 0 R
>>
startxref
274
%%EOF"""

# Sample document contents for different document types
SAMPLE_DOCUMENTS = {
    "invoice": """ACME Corporation
123 Business Ave
Anytown, ST 12345

INVOICE

Invoice #: INV-2024-001
Date: January 15, 2024
Due Date: February 15, 2024

Bill To:
John Smith
456 Customer St
Somewhere, ST 67890

Description                 Qty    Rate     Amount
Consulting Services         10     $150.00  $1,500.00
Project Management          1      $500.00  $500.00

Subtotal:                                   $2,000.00
Tax (8.5%):                                 $170.00
Total:                                      $2,170.00

Payment Terms: Net 30 days
Thank you for your business!
""",

    "medical_report": """Central Medical Center
789 Health Drive
Medical City, MC 54321

PATIENT MEDICAL REPORT

Patient: Jane Doe
DOB: 03/15/1980
Date of Service: January 20, 2024
Provider: Dr. Sarah Johnson, MD

CHIEF COMPLAINT:
Annual physical examination

VITAL SIGNS:
Blood Pressure: 120/80 mmHg
Heart Rate: 72 bpm
Temperature: 98.6°F
Weight: 140 lbs

ASSESSMENT:
Patient is in good health. All vital signs normal.
Recommended annual lab work completed.

PLAN:
Continue current exercise routine.
Follow up in 12 months for next annual physical.

Dr. Sarah Johnson, MD
License #: MD123456
""",

    "insurance_eob": """Health Insurance Company
PO Box 12345
Insurance City, IC 98765

EXPLANATION OF BENEFITS

Member: Robert Wilson
Member ID: HIC123456789
Date of Service: January 10, 2024
Provider: City Hospital

Service Description: Emergency Room Visit
Billed Amount: $850.00
Insurance Paid: $680.00
Patient Responsibility: $170.00

Deductible Applied: $100.00
Copayment: $50.00
Coinsurance (20%): $20.00

This is not a bill. Please retain for your records.
Questions? Call member services at 1-800-HEALTH1
""",

    "property_deed": """WARRANTY DEED

STATE OF EXAMPLE
COUNTY OF SAMPLE

KNOW ALL MEN BY THESE PRESENTS, that John Seller and Mary Seller, husband and wife,
Grantors, for and in consideration of Ten Dollars ($10.00) and other good and valuable
consideration, the receipt and sufficiency of which is hereby acknowledged, do hereby
grant, bargain, sell and convey unto Robert Buyer and Susan Buyer, husband and wife,
as joint tenants with right of survivorship, Grantees, the following described real estate:

LOT 15, BLOCK 3, SUNNY MEADOWS SUBDIVISION, according to the recorded plat thereof,
situated in Sample County, State of Example.

Property Address: 123 Maple Street, Hometown, EX 12345

TO HAVE AND TO HOLD the same, together with all the appurtenances thereunto belonging,
unto the said Grantees, their heirs and assigns forever.

Dated this 15th day of January, 2024.

John Seller                    Mary Seller
Grantor                        Grantor

STATE OF EXAMPLE
COUNTY OF SAMPLE

The foregoing instrument was acknowledged before me this 15th day of January, 2024.

                              Notary Public
My commission expires: 12/31/2025
""",

    "tax_return": """U.S. Individual Income Tax Return
Form 1040
For the year 2023

Name: Michael Taxpayer
SSN: XXX-XX-1234
Address: 789 Tax Lane, Fiscal City, TX 75001

Filing Status: Single

Income:
Wages, salaries, tips (Form W-2): $65,000
Interest income: $120
Total Income: $65,120

Adjusted Gross Income: $65,120

Standard Deduction: $13,850
Taxable Income: $51,270

Tax: $5,739
Federal tax withheld: $6,200
Refund: $461

Signed: Michael Taxpayer
Date: April 10, 2024
""",

    "pet_medical": """Happy Paws Veterinary Clinic
456 Pet Care Road
Animal Town, AT 98765

VETERINARY MEDICAL RECORD

Pet Name: Fluffy
Species: Feline (Domestic Shorthair)
Owner: Lisa Peterson
Date of Visit: January 25, 2024

REASON FOR VISIT:
Annual wellness examination and vaccinations

EXAMINATION:
Weight: 12 lbs
Temperature: 101.5°F (normal)
Heart Rate: 180 bpm
Overall condition: Excellent

SERVICES PROVIDED:
- Physical examination
- FVRCP vaccination
- Rabies vaccination
- Fecal examination (negative)

RECOMMENDATIONS:
Continue current diet and exercise.
Next visit in 12 months for annual wellness.

Dr. Amanda Vet, DVM
License #: VET789012
""",

    "financial_statement": """First National Bank
Monthly Account Statement

Account Holder: Sarah Williams
Account Number: ****1234
Statement Period: December 1-31, 2023

Beginning Balance: $2,850.45

DEPOSITS:
12/01 Direct Deposit - Salary        $3,200.00
12/15 Direct Deposit - Salary        $3,200.00
Total Deposits:                      $6,400.00

WITHDRAWALS:
12/02 Online Payment - Mortgage      $1,850.00
12/05 ATM Withdrawal                 $100.00
12/10 Check #1245 - Utilities       $150.00
12/15 Online Payment - Credit Card   $500.00
Total Withdrawals:                   $2,600.00

Ending Balance: $6,650.45

Average Daily Balance: $4,750.23
Days in Statement Period: 31
""",
}

# LLM response templates for different document types
LLM_RESPONSES = {
    "invoice": {
        "suggested_path": "Person/ACME_Corporation/Financial/2024-01-15_consulting_invoice.pdf",
        "filename": "2024-01-15_consulting_invoice.pdf",
        "reasoning": "This is an invoice from ACME Corporation dated January 15, 2024 for consulting services. Following the Financial category taxonomy rules, it should be organized under the company name with the service date."
    },

    "medical_report": {
        "suggested_path": "Person/Jane_Doe/Medical/2024-01-20_annual_physical.pdf",
        "filename": "2024-01-20_annual_physical.pdf",
        "reasoning": "Medical report for Jane Doe from January 20, 2024 annual physical examination. Categorized under Medical following taxonomy rules for personal medical documents."
    },

    "insurance_eob": {
        "suggested_path": "Person/Robert_Wilson/Medical/Billing/2024-01-10_emergency_room_eob.pdf",
        "filename": "2024-01-10_emergency_room_eob.pdf",
        "reasoning": "Explanation of Benefits (EOB) for Robert Wilson's emergency room visit on January 10, 2024. Placed in Medical/Billing subcategory as specified in taxonomy rules."
    },

    "property_deed": {
        "suggested_path": "Property/Sunny_Meadows/Purchase/2024-01-15_warranty_deed.pdf",
        "filename": "2024-01-15_warranty_deed.pdf",
        "reasoning": "Warranty deed dated January 15, 2024 for property at Sunny Meadows Subdivision. Categorized under Property/Purchase following taxonomy rules for property transactions."
    },

    "tax_return": {
        "suggested_path": "Person/Michael_Taxpayer/Tax/2023/tax_return.pdf",
        "filename": "2023_tax_return.pdf",
        "reasoning": "Tax return for Michael Taxpayer for year 2023. Following taxonomy rules, tax returns use year-based naming and are stored in the Tax category."
    },

    "pet_medical": {
        "suggested_path": "Pets/Fluffy/Medical/2024-01-25_annual_wellness_exam.pdf",
        "filename": "2024-01-25_annual_wellness_exam.pdf",
        "reasoning": "Veterinary medical record for pet Fluffy dated January 25, 2024. Categorized under Pets/Medical following taxonomy rules for pet healthcare documents."
    },

    "financial_statement": {
        "suggested_path": "Person/Sarah_Williams/Financial/2023-12-31_bank_statement.pdf",
        "filename": "2023-12-31_bank_statement.pdf",
        "reasoning": "Bank statement for Sarah Williams for December 2023. Categorized under Financial following taxonomy rules for personal financial documents."
    }
}

# Test taxonomy content
TEST_TAXONOMY = """# Test Document Organization Taxonomy

## Core Principles
- Filenames: `YYYY-MM-DD_descriptive_name.ext`
- Date Priority: Document date, creation date, current date

## Categories

### Medical
- **Path:** `Person/{Name}/Medical/{date}_{description}.pdf`
- **Subcategories:**
  - `Billing`: For insurance EOBs and medical bills
- **Rules:**
  - If document contains "Explanation of Benefits" or "EOB", use Billing subcategory
  - Medical reports, lab results go in main Medical category

### Financial  
- **Path:** `Person/{Name}/Financial/{date}_{description}.pdf`
- **Rules:**
  - Invoices, receipts, bank statements
  - Tax returns: `Person/{Name}/Tax/{YYYY}/tax_return.pdf`

### Property
- **Path:** `Property/{Location}/{Type}/{date}_{description}.pdf`
- **Types:** `Purchase`, `Insurance`, `Maintenance`, `Taxes`
- **Rules:**
  - Deeds go in Purchase subcategory
  - Insurance policies go in Insurance subcategory

### Pets
- **Path:** `Pets/{Pet_Name}/{Category}/{date}_{description}.pdf`
- **Categories:** `Medical`, `Insurance`, `Registration`
- **Rules:**
  - Veterinary records go in Medical category

### Other
- **Path:** `Other/{date}_{description}.pdf`
- **Rules:** For documents that don't fit other categories
"""

# Common file extensions for testing
TEST_FILE_EXTENSIONS = [".pdf", ".txt", ".doc", ".docx"]

# Error scenarios for testing
ERROR_SCENARIOS = {
    "invalid_json": "This is not valid JSON response",
    "missing_fields": '{"suggested_path": "test/path.pdf", "reasoning": "missing filename field"}',
    "wrong_extension": '{"suggested_path": "test/path.txt", "filename": "test.txt", "reasoning": "wrong extension for PDF file"}',
    "api_error": "API Error: Invalid API key",
    "rate_limit": "Rate limit exceeded: Too many requests"
}

# Sample configuration data
SAMPLE_CONFIGS = {
    "minimal": {
        "gemini": {
            "api_key": "test-key",
            "model": "gemini-2.0-flash"
        }
    },

    "full": {
        "gemini": {
            "api_key": "full-test-key",
            "model": "gemini-2.0-flash",
            "temperature": 0.8,
            "timeout": 60
        }
    },

    "custom_model": {
        "gemini": {
            "api_key": "custom-key",
            "model": "gemini-1.5-pro",
            "temperature": 0.5,
            "timeout": 120
        }
    }
}
