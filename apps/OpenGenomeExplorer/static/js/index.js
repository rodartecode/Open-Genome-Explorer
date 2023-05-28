import { initializeApp } from 'https://www.gstatic.com/firebasejs/9.22.1/firebase-app.js'

// Add Firebase products that you want to use
import { getAuth, onAuthStateChanged, signInWithCustomToken, browserSessionPersistence  } from 'https://www.gstatic.com/firebasejs/9.22.1/firebase-auth.js'
import { getDatabase } from 'https://www.gstatic.com/firebasejs/9.22.1/firebase-database.js'

// Import the functions you need from the SDKs you need
// TODO: Add SDKs for Firebase products that you want to use
// https://firebase.google.com/docs/web/setup#available-libraries

// Your web app's Firebase configuration
// For Firebase JS SDK v7.20.0 and later, measurementId is optional
const firebaseConfig = {
apiKey: "AIzaSyCezKBpHBgfohekmUX6HdsHTnlcPd-Ss2g",
authDomain: "open-genome-explorer.firebaseapp.com",
databaseURL: "https://open-genome-explorer-default-rtdb.firebaseio.com",
projectId: "open-genome-explorer",
storageBucket: "open-genome-explorer.appspot.com",
messagingSenderId: "66972289733",
appId: "1:66972289733:web:0378adea8262164c2afeac",
measurementId: "G-R4X3QLPK7V"
};

// Initialize Firebase
const firebase_app = initializeApp(firebaseConfig);

const fb_database = getDatabase();
const auth = getAuth();

console.log("auth:", auth)

// This will be the object that will contain the Vue attributes
// and be used to initialize it.
let app = {};


// Given an empty app object, initializes it filling its attributes,
// creates a Vue instance, and then initializes the Vue instance.
let init = (app) => {

    // This is the Vue data.
    app.data = {
        query: "",
        meow: "",
        reply_meow: [],
        reply_mode: false,
        meow_id: 0,
        meows: [],
        user_rows: [],
        select_buttons: [true, false, false],
        meows_loading: false,
        your_meows_loading: false,
        recent_meows_loading: false,
        last_chosen_user_id: 0,
        in_specified_user_meow: false,
        user: null,
        user_snps: [],
        hide_upload: true,
        uploading: false,
        uploaded_file: "",
        upload_done: false,
        start_index: 0,
        end_index: 25,
        page_size: 25,
        cur_page_num: 0,
    };

    app.enumerate = (a) => {
        // This adds an _idx field to each element of the array.
        let k = 0;
        a.map((e) => {e._idx = k++;});
        return a;
    };

    app.get_time = function (timestamp) {
        return Sugar.Date(timestamp + "Z").relative()
    }

    app.set_follow = function (user_id) {
        console.log("follow!")
        axios.get(set_follow_url, {params: {user_id: user_id}})
            .then(function (result) {
                axios.get(search_url).then(function (r) {
                    app.vue.user_rows = r.data.user_rows;
                })
            });
    }

    app.post_remeow = function (remeow) {
            axios.get(post_meow_url, {params: {m: remeow}})
                .then(function (result) {
                    axios.get(get_meows_url).then(function (r) {
                        app.vue.meows = app.enumerate(r.data.meows);
                    })
                });
    }

    app.post_meow = function () {
        if (app.vue.reply_mode) {
            app.post_reply(app.vue.meow)
        }
        else {
        axios.get(post_meow_url, {params: {m: app.vue.meow}})
            .then(function (result) {
                if (app.vue.select_buttons[0]) {
                    app.get_meows();
                }
                else if (app.vue.select_buttons[1]) {
                    app.your_meows();
                }
                else if (app.vue.select_buttons[2]) {
                    app.recent_meows();
                }
                else if (app.vue.in_specified_user_meow) {
                    app.get_user_meows(last_chosen_user_id);
                }
            });
        }
    }
    app.post_reply = function (reply) {
        axios.get(post_reply_url, {params: {reply: reply, meow_id: app.vue.meow_id}})
            .then(function (result) {
                    app.get_replies(app.vue.meow_id)
            });
    }

    app.get_replies = function (meow_id) {
        axios.get(get_replies_url, {params: {meow_id: meow_id}})
            .then(function (result) {
                for (let i = 0; i < app.vue.meows.length; i++) {
                    if (app.vue.meows[i].id == meow_id) {
                        app.vue.reply_meow = app.vue.meows[i];
                    }
                }
            
                app.vue.meows = app.enumerate(result.data.replies);
                app.vue.reply_mode = true;
                app.vue.meow_id = meow_id
                app.vue.in_specified_user_meow = false;
            });
    }

    app.get_meows = function () {
        select_buttons=[true, false, false];
        axios.get(get_meows_url)
            .then(function (result) {
                app.vue.meows = app.enumerate(result.data.meows);
                app.vue.reply_mode = false;
                app.vue.meows_loading = false;
                app.vue.in_specified_user_meow = false;
            });
    }

    app.get_user_meows = function (user_id) {
        axios.get(get_user_meows_url, {params: {user_id: user_id}})
            .then(function (result) {
                app.vue.meows = app.enumerate(result.data.meows);
                app.vue.reply_mode = false;
                app.vue.last_chosen_user_id = user_id;
                app.vue.in_specified_user_meow = true;
            });
    }

    app.your_meows = function () {
        axios.get(your_meows_url)
            .then(function (result) {
                app.vue.meows = app.enumerate(result.data.meows);
                app.vue.reply_mode = false;
                app.vue.your_meows_loading = false;
                app.vue.in_specified_user_meow = false;
            });
    }

    app.recent_meows = function () {
        axios.get(get_recent_meows_url)
            .then(function (result) {
                app.vue.meows = app.enumerate(result.data.meows);
                app.vue.reply_mode = false;
                app.vue.recent_meows_loading = false;
                app.vue.in_specified_user_meow = false;
            });
    }

    app.upload_complete = function (file_name, file_type) {
        app.vue.uploading = false;
        app.vue.upload_done = true;
        app.vue.uploaded_file = file_name;
        app.get_snps();
    };

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
        axios.get(get_snps_url).then(function (r) {
            app.vue.user_snps = app.enumerate(r.data.user_snps);
            app.vue.hide_upload = false;

        })
    };

    app.upload_file = function (event) {
        // We need the event to find the file.
        // TODO: Can't handle uploading full size file for some reason
        let self = this;
        // Reads the file.
        let input = event.target;
        let file = input.files[0];
        if (file) {
            self.uploading = true;
            let file_type = file.type;
            let file_name = file.name;
            let full_url = file_upload_url + "&file_name=" + encodeURIComponent(file_name)
                + "&file_type=" + encodeURIComponent(file_type);
            // Uploads the file, using the low-level streaming interface. This avoid any
            // encoding.
            console.log(file)
            app.vue.uploading = true;
            let req = new XMLHttpRequest();
            req.addEventListener("load", function () {
                app.upload_complete(file_name, file_type)
            });
            req.open("PUT", full_url, true);
            req.send(file);
        }
    };

    app.search = function () {
        console.log("searching!")
            axios.get(search_url, {params: {q: app.vue.query}})
                .then(function (result) {
                    app.vue.user_rows = result.data.user_rows;
                    if (result.length == 0) {
                        axios.get(search_url).then(function (r) {
                            app.vue.user_rows = r.data.user_rows;
                            app.vue.reply_mode = false;
                            app.vue.in_specified_user_meow = false;
                        })
                    }
                });
    }

    app.form_reset = function() {
        app.vue.meow = "";
      }

    // This contains all the methods.
    app.methods = {
        // Complete as you see fit.
        post_meow: app.post_meow,
        post_reply: app.post_reply,
        get_meows: app.get_meows,
        your_meows: app.your_meows,
        post_remeow: app.post_remeow,
        get_replies: app.get_replies,
        search: app.search,
        set_follow: app.set_follow,
        get_user_meows: app.get_user_meows,
        recent_meows: app.recent_meows,
        get_time: app.get_time,
        form_reset: app.form_reset,
        upload_file: app.upload_file,
        upload_complete: app.upload_complete,
        get_snps: app.get_snps,
        retrieve_snps: app.retrieve_snps,
    };

    // This creates the Vue instance.
    app.vue = new Vue({
        el: "#vue-target",
        data: app.data,
        methods: app.methods
    });

    // And this initializes it.
    app.init = () => {
        // onAuthStateChanged(auth, (user) => {
        //     if (user) {
        //       // User is signed in, see docs for a list of available properties
        //       // https://firebase.google.com/docs/reference/js/auth.user
        //       const uid = user.uid;
        //       app.vue.user = user;
        //       // ...
        //     } else {
        //       // User is signed out
        //       // ...
        //       axios.post(auth_verify_url).then(function (r) {
        //         console.log("custom_token:", r.data.custom_token)
        //         signInWithCustomToken(auth, r.data.custom_token)
        //         .then((userCredential) => {
        //             // Signed in
        //             const user = userCredential.user;
        //             // ...
        //         })
        //         .catch((error) => {
        //             const errorCode = error.code;
        //             const errorMessage = error.message;
        //             console.log(errorCode)
        //             console.log(errorMessage)
        //             console.log(error)
        //             // ...
        //         });
        //     })
        //     }
        //   });

        axios.get(get_meows_url).then(function (r) {
            app.vue.meows = app.enumerate(r.data.meows);
        })

        app.get_snps();

        axios.get(search_url).then(function (r) {
            app.vue.user_rows = r.data.user_rows;
            console.log(app.vue.user_rows)
            console.log(search_url)
        })

    };

    // Call to the initializer.
    app.init();
};

// This takes the (empty) app object, and initializes it,
// putting all the code i
init(app);