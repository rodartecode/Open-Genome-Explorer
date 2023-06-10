# Open Genome Explorer

## About Open Genome Explorer

![Logo](images/logo.PNG)

Open Genome Explorer is a web app that utilizes the genetic information the user uploads in order to provide insights about their genome. By using data provided by open source SNP database [OpenSNP](https://opensnp.org/), the user may learn more about their health traits and genetic risk factors based on the genetic information they upload.

## Usage

* Create an account using built-in py4web auth and sign in.
* Upload your SNP array from sources like 23andMe or AncestryDNA. `test-genome.txt` is included for testing. 
![Upload](images/home.PNG)
* The data in the file should follow the format:

| rsid      | chromosome | position | genotype |
|-----------|------------|----------|----------|
| rs2478267 | 1          | 7584814  | GG       |
| rs2013624 | 1          | 7588413  | CC       |
| ...       | ...        | ...      | ...      |

* Once the file has been processed, any data matching known good SNP data will be displayed in a table.
![Results Table](images/results.PNG)
* Sort the table by any column by clicking on the column.
* Search for results by rsid or summary by typing into the rsid or summary box.
![Search Results](images/search.PNG)
* Clicking on a URL will open the openSNP page containing detailed results in a new tab.
* Pressing Share will add your SNP to a public page that any user can see.
* Pressing Comment will allow you to add comments to a SNP.
* Pressing on a SNP will load that SNP's page and all comments associated.

## Initial Setup

### Install Dependencies

From the root directory run

```bash
pip -r requirements.txt
```

### Run

From the root directory run the app with

```bash
py4web run apps
```

## Deployment

For instructions related to deployment, see `deployment_tools/gae/README.md`

## Implementation

* This app is implemented using the Py4web framework, Vue.js JavaScript framework, Bulma css, and Font Awesome icons, as well as open-source data provided by OpenSNP.
* The landing page acts as the app's index and does not require authorization. Pressing `Get Started` will lead the user through the instructions page and then to the home page, which requires authorization.
* Genomic information uploaded by the user is parsed and compared to known good SNP data taken from OpenSNP, stored in `good_snp_data.json`. A test file is provided, `test-genome.txt`. Every match found is added to a table, SNP. A separate function retrieves the SNPs, which is returned to and filtered by the frontend to be displayed. Uploading another file will insert rows into the table that were not there before, or update them otherwise.
* Sorting the table occurs as a request to the backend, `get_sorted_SNPs()`, which retrieves data from the SNPs table in an order specified by the frontend. This data is updated in the frontend as a `user_snps` variable.
* The search functionality occurs entirely in the frontend, and filters `user_snps` into `display_snps` based on the search parameters, which is then displayed.
* Shared SNPs are stored in a shared_SNP table by the backend in `share_snp()`, which contains publically shared SNPs and is referred to by comments, which are also handled by the backend in `add_comment()`.
* The shared SNPs page makes a request to the backend to retrieve shared SNPs from the db in `get_shared_snps()` and is rendered by the frontend using the template `shared_snp.html`.