# Document Organization Taxonomy

## Core Principles

*   Filenames: `YYYY-MM-DD_descriptive_name.ext` (or `YYYY_descriptive_name.ext` for annual documents).
*   Date Priority (highest to lowest):
    1.  Document-specific date (invoice, service, etc.)
    2.  Date mentioned in document content.
    3.  Document creation date.
    4.  Current date (as a last resort).
* Descriptive Names: Clear, meaningful, use underscores, avoid non-standard abbreviations.

## Categories

### 1. Medical

*   **Path:** `Person/{Name}/Medical/{Subcategory}/{date}_{description}.pdf`
*   **Subcategories:**
    *   `Billing`: For insurance EOBs.
    *   *(Default)*:  Use no subcategory for doctor visits, lab results, medical bills.
* **Rules:**
    *  If the document contains "Explanation of Benefits" or "EOB", it should go in the `Billing` subcategory.
*   **Examples:**
    *   `Lab Report for Morticia Addams.pdf`  ->  `Person/Morticia/Medical/2024-02-01_blood_lab_results.pdf`
    *   `EOB Statement.pdf`  ->  `Person/Wednesday/Medical/Billing/2024-01-15_anthem_eob.pdf`

### 2. Property

*   **Path:** `Property/{Location}/{Type}/{date}_{description}.pdf`
*   **Types:** `Purchase`, `Insurance`, `Maintenance`, `Taxes`
*   **Date Priority (Property-Specific):**
    1.  Closing/purchase date (for transactions).
    2.  Document date (for legal papers).
    3.  Service date (for maintenance).
* **Rules:**
     * If document contains the word "Deed", it goes into `Purchase`.
     * If document contains the word "Insurance", it goes into `Insurance`.
     * If document contains words like, "Repairs", "Maintenance", it goes into `Maintenance`.
*   **Examples:**
    *   `Deed of Trust.pdf`  ->  `Property/Creepsville/Purchase/2024-01-15_deed_of_trust.pdf`
    *   `Home Insurance Policy.pdf`  ->  `Property/FogHollow/Insurance/2024_home_insurance_policy.pdf`

### 3. Financial

*   **Path:** `Person/{Name}/Financial/{Subcategory}/{date}_{description}.pdf`  (or `Person/{Name}/Tax/{YYYY}/{description}.pdf` for tax returns)
*  **Subcategories:**
        * `Investments`
        * `Insurance`
        * `Tax`
        * *(Default): Use no subcategory for general financial documents.*

*   **Rules:**
    *   Tax returns: `Person/{Name}/Tax/{YYYY}/tax_return.pdf`
    * If document contains "Investment Statement", place in `Investments`.
    * If document contains "Insurance policy", place in `Insurance`.
*   **Examples:**
    *   `1099-INT.pdf`  ->  `Person/Gomez/Financial/2024_1099_int.pdf`
    *   `Tax Return 2023.pdf`  ->  `Person/Morticia/Tax/2023/tax_return.pdf`
    *  `Life Insurance Policy.pdf` -> `Person/Wednesday/Financial/Insurance/2024-03-20_life_insurance.pdf`

### 4. Pet Records

*   **Path:** `Pets/{Pet_Name}/{Category}/{date}_{description}.pdf`
*   **Categories:** `Medical`, `Insurance`, `Registration`
* **Rules:**
    * If document contains "Vet", "Veterinary", place in `Medical`.
    * If document contains "Pet Insurance", place in `Insurance`.
    * For exotic pets, include species in description.
*   **Examples:**
    *   `Lion Health Report.pdf`  ->  `Pets/Kitty_Kat/Medical/2024-02-15_lion_annual_checkup.pdf`
    *   `Exotic Pet Insurance.pdf` -> `Pets/Kitty_Kat/Insurance/2024_exotic_pet_policy.pdf`
    *   `Vulture Health Check.pdf` -> `Pets/Socrates/Medical/2024-03-10_vulture_wellness_exam.pdf`
    *   `Exotic Bird Permit.pdf` -> `Pets/Socrates/Registration/2024_exotic_bird_permit.pdf`

### 5. Family Members

*   **Rules:** These determine the `{Name}` to use in paths for other categories.
    *   Gomez Addams  ->  `Person/Gomez`
    *   Morticia Addams  ->  `Person/Morticia`
    *   Wednesday Addams  ->  `Person/Wednesday`
    *   Pugsley Addams  ->  `Person/Pugsley`
    *   Uncle Fester Addams  ->  `Person/Fester`

### 6. Property Locations

*   **Rules:** These determine the `{Location}` to use in the `Property` category path.
    *   0001 Cemetery Lane  ->  `Property/Creepsville`
    *   13 Gothic Avenue  ->  `Property/Shadytown`
    *   99 Batwing Boulevard  ->  `Property/FogHollow`

### 7. Pets

*   **Rules:** These determine the `{Pet_Name}` to use in the `Pets` category path.
    *   Kitty Kat (lion)  ->  `Pets/Kitty_Kat`
    *   Socrates (vulture)  ->  `Pets/Socrates`

### 8. Other

*   **Path:** `Other/{date}_{description}.pdf`
*   **Rules:** Use for documents that don't fit any other category.
* **Rules:**
    *   Non-family persons -> `Person/Other/{date}_{name}`

### Precedence
* Property documents are categorized before medical documents.