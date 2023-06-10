let app = {};

let init = (app) => {

    app.data = {
        comment: "",
        shared_snp_id: 0,
        comments: [],
    };

    app.enumerate = (a) => {
        let k = 0;
        a.map((e) => {e._idx = k++;});
        return a;
    };

    app.get_comments = function () {
        axios.get(get_comments_url).then(function (r) {
            app.vue.comments = app.enumerate(r.data.comments);
        })
    };

    app.form_reset = function() {
        app.vue.comment = "";
    }

    app.add_comment = function () {
        axios.get(add_comment_url, {params: {shared_snp_id: app.vue.shared_snp_id, content: app.vue.comment}})
            .then(function (result) {
                    app.get_comments(app.vue.shared_snp_id)
            });
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

        app.get_comments();

    };

    app.init();
};

init(app);