let app = {};

let init = (app) => {

    app.data = {
        user: null,
        user_snps: [],
        display_snps: [],
        start_index: 0,
        end_index: 25,
        page_size: 25,
        cur_page_num: 0,
        file_name: "",
        file_type: "",
        file_date: "",
        file_path: "",
        file_size: "",
        search_summary: "",
        search_rsid: "",
        row_clicked: false,
        column_sorted: null,
    };

    app.enumerate = (a) => {
        let k = 0;
        a.map((e) => {e._idx = k++;});
        return a;
    };

    app.search = function () {
        if (app.vue.search_rsid.length > 0) {
            app.vue.display_snps = app.vue.user_snps.filter(function(item) {
                return item.rsid.toLowerCase().indexOf(app.vue.search_rsid.toLowerCase()) >= 0
            })
        }
        else if (app.vue.search_summary.length > 0) {
            app.vue.display_snps = app.vue.user_snps.filter(function(item) {
                return item.summary.toLowerCase().indexOf(app.vue.search_summary.toLowerCase()) >= 0
            })
        }
        else {
            app.vue.display_snps = app.vue.user_snps;
        }
    }

    app.retrieve_snps = function (page_num) {
        // TODO: Check for issues with str types, use parseInt
        if (page_num < 0 || ((page_num * app.vue.page_size) >= (app.vue.user_snps.length) )) {

        }
        else if (app.vue.cur_page_num > page_num) {
            app.vue.start_index -= app.vue.page_size;
            app.vue.end_index -= app.vue.page_size;
            app.vue.cur_page_num -= 1;
            if (app.vue.start_index < 0) {
                app.vue.cur_page_num = 0;
                app.vue.start_index = 0;
                app.vue.end_index = app.vue.page_size;
            }
        }
        else if (app.vue.cur_page_num < page_num) {
            app.vue.start_index += app.vue.page_size;
            app.vue.end_index += app.vue.page_size;
            app.vue.cur_page_num += 1;
            // TODO: Consider what to do with cur page num here
            if (app.vue.end_index >= app.vue.user_snps.length) {
                app.vue.start_index = app.vue.end_index - app.vue.page_size;
                app.vue.end_index = app.vue.user_snps.length-1;
            }
        }
    };

    app.get_snps = function () {
        axios.get(get_shared_snps_url).then(function (r) {
            app.vue.user_snps = app.enumerate(r.data.user_snps);
            app.vue.hide_upload = false;
            app.vue.display_snps = app.vue.user_snps;
        })
    };

    // Sort the table by the clicked attribute
    app.sort_table = function (column_num) {
        // Sortable attributes
        let attrs = [
            "rsid", 
            "allele1", 
            "allele2", 
            "summary", 
            "weight_of_evidence", 
            "url"
        ];
        let sort = "desc";
        let attr = attrs[column_num];

        // First sort is always descending; If already sorted, then sort by ascending
        if (app.vue.column_sorted == attr) {
            app.vue.column_sorted = null;
            sort = "asc";
        } else {
            app.vue.column_sorted = attrs[column_num];
        }

        // Request sorted SNPs
        axios.get(get_shared_sorted_snps_url, {params: {
            attr: attrs[column_num],
            sort: sort,
        }})
        .then(function(result) {
            app.vue.user_snps = app.enumerate(result.data.user_snps);
            app.vue.display_snps = app.vue.user_snps;
        })
    }

    app.methods = {
        get_snps: app.get_snps,
        retrieve_snps: app.retrieve_snps,
        search: app.search,
        sort_table: app.sort_table,
    };

    app.vue = new Vue({
        el: "#vue-target",
        data: app.data,
        methods: app.methods
    });

    app.init = () => {

        app.get_snps();

    };

    app.init();
};

init(app);