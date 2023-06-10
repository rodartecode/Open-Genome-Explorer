let app = {};

let init = (app) => {

    app.data = {
        user: null,
        user_snps: [],
        display_snps: [],
        hide_upload: true,
        uploading: false,
        uploaded_file: "",
        upload_done: false,
        start_index: 0,
        end_index: 25,
        page_size: 25,
        cur_page_num: 0,
        file_name: "",
        file_type: "",
        file_date: "",
        file_path: "",
        file_size: "",
        download_url: "",
        deleting: false,
        delete_done: false,
        use_gcs: false,
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

    // The following code was adapted from Luca's tutorial in Unit 19
    // https://learn-py4web.github.io/unit19.html
    app.file_info = function () {
        if (app.vue.file_path) {
            let info = "";
            if (app.vue.file_size) {
                info = humanFileSize(app.vue.file_size.toString(), si=true);
            }
            if (app.vue.file_type) {
                if (info) {
                    info += " " + app.vue.file_type;
                } else {
                    info = app.vue.file_type;
                }
            }
            if (info) {
                info = " (" + info + ")";
            }
            if (app.vue.file_date) {
                let d = new Sugar.Date(app.vue.file_date + "+00:00");
                info += ", uploaded " + d.relative();
            }
            return app.vue.file_name + info;
        } else {
            return "";
        }
    }

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

    app.set_result = function (r) {
        // Sets the results after a server call.
        app.vue.file_name = r.data.file_name;
        app.vue.file_type = r.data.file_type;
        app.vue.file_date = r.data.file_date;
        app.vue.file_path = r.data.file_path;
        app.vue.file_size = r.data.file_size;
        app.vue.download_url = r.data.download_url;
    }

    app.upload_file_gcs = function (event) {
        let input = event.target;
        let file = input.files[0];
        if (file) {
            app.vue.uploading = true;
            let file_type = file.type;
            let file_name = file.name;
            let file_size = file.size;
            // Requests the upload URL.
            axios.post(obtain_gcs_url, {
                action: "PUT",
                mimetype: file_type,
                file_name: file_name
            }).then ((r) => {
                let upload_url = r.data.signed_url;
                let file_path = r.data.file_path;
                // Uploads the file, using the low-level interface.
                let req = new XMLHttpRequest();
                // We listen to the load event = the file is uploaded, and we call upload_complete.
                // That function will notify the server `of the location of the image.
                req.addEventListener("load", function () {
                    app.upload_complete(file_name, file_type, file_size, file_path);
                });
                // TODO: if you like, add a listener for "error" to detect failure.
                req.open("PUT", upload_url, true);
                req.send(file);
            });
        }
    }

    app.upload_complete = function (file_name, file_type, file_size, file_path) {
        // We need to let the server know that the upload was complete;
        axios.post(notify_url, {
            file_name: file_name,
            file_type: file_type,
            file_path: file_path,
            file_size: file_size,
        }).then( function (r) {
            app.vue.uploading = false;
            app.vue.file_name = file_name;
            app.vue.file_type = file_type;
            app.vue.file_path = file_path;
            app.vue.file_size = file_size;
            app.vue.file_date = r.data.file_date;
            app.vue.download_url = r.data.download_url;
            app.get_snps();
        });
    }

    app.delete_file = function () {
        if (!app.vue.delete_confirmation) {
            // Ask for confirmation before deleting it.
            app.vue.delete_confirmation = true;
        } else {
            // It's confirmed.
            app.vue.delete_confirmation = false;
            app.vue.deleting = true;
            // Obtains the delete URL.
            let file_path = app.vue.file_path;
            axios.post(obtain_gcs_url, {
                action: "DELETE",
                file_path: file_path,
            }).then(function (r) {
                let delete_url = r.data.signed_url;
                if (delete_url) {
                    // Performs the deletion request.
                    let req = new XMLHttpRequest();
                    req.addEventListener("load", function () {
                        app.deletion_complete(file_path);
                    });
                    // TODO: if you like, add a listener for "error" to detect failure.
                    req.open("DELETE", delete_url);
                    req.send();

                }
            });
        }
    };

    app.deletion_complete = function (file_path) {
        // We need to notify the server that the file has been deleted on GCS.
        axios.post(delete_url, {
            file_path: file_path,
        }).then (function (r) {
            // Poof, no more file.
            app.vue.deleting =  false;
            app.vue.file_name = null;
            app.vue.file_type = null;
            app.vue.file_date = null;
            app.vue.file_path = null;
            app.vue.download_url = null;
        })
    }

    app.download_file = function () {
        if (app.vue.download_url) {
            let req = new XMLHttpRequest();
            req.addEventListener("load", function () {
                app.do_download(req);
            });
            req.responseType = 'blob';
            req.open("GET", app.vue.download_url, true);
            req.send();
        }
    };

    app.do_download = function (req) {
        // This Machiavellic implementation is thanks to Massimo DiPierro.
        // This creates a data URL out of the file we downloaded.
        let data_url = URL.createObjectURL(req.response);
        // Let us now build an a tag, not attached to anything,
        // that looks like this:
        // <a href="my data url" download="myfile.jpg"></a>
        let a = document.createElement('a');
        a.href = data_url;
        a.download = app.vue.file_name;
        // and let's click on it, to do the download!
        a.click();
        // we clean up our act.
        a.remove();
        URL.revokeObjectURL(data_url);
    };

    // Thank you Luca and Massimo

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

    app.share_snp = function (snp) {
        axios.post(share_snp_url, {
            snp: snp,
        }).then( function (r) {
        });
    };

    app.get_snps = function () {
        axios.get(get_snps_url).then(function (r) {
            app.vue.user_snps = app.enumerate(r.data.user_snps);
            app.vue.hide_upload = false;
            app.vue.display_snps = app.vue.user_snps;
        })
    };

    app.computed = {
        file_info: app.file_info,
    };

    app.upload_complete_nogcs = function (file_name, file_type){
        app.vue.uploading = false;
        app.vue.upload_done = true;
        app.vue.uploaded_file = file_name;
        app.get_snps();
    }

    app.upload_file_nogcs = function (event){
        let input = event.target;
        let file = input.files[0];
        if (file) {
            app.vue.uploading = true;
            let file_type = file.type;
            let file_name = file.name;
            let full_url = file_upload_url + "&file_name=" + encodeURIComponent(file_name) + "&file_type" + encodeURIComponent(file_type);
            let req = new XMLHttpRequest();
            req.addEventListener("load", function(){
                app.upload_complete_nogcs(file_name, file_type);
            });
            req.open("PUT", full_url, true);
            req.send(file);
            //get_snps();
        }
    }

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
        axios.get(get_sorted_snps_url, {params: {
            attr: attrs[column_num],
            sort: sort,
        }})
        .then(function(result) {
            app.vue.user_snps = app.enumerate(result.data.user_snps);
            app.vue.display_snps = app.vue.user_snps;
        })
    }

    app.methods = {
        upload_file_nogcs: app.upload_file_nogcs,
        upload_file_gcs: app.upload_file_gcs,
        upload_complete: app.upload_complete,
        get_snps: app.get_snps,
        retrieve_snps: app.retrieve_snps,
        delete_file: app.delete_file,
        download_file: app.download_file,
        search: app.search,
        sort_table: app.sort_table,
        share_snp: app.share_snp,
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