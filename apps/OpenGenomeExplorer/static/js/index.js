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

// console.log("auth:", auth)

// This will be the object that will contain the Vue attributes
// and be used to initialize it.
let app = {};


// Given an empty app object, initializes it filling its attributes,
// creates a Vue instance, and then initializes the Vue instance.
let init = (app) => {

    // This is the Vue data.
    app.data = {
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
        file_name: "",
        file_type: "",
        file_date: "",
        file_path: "",
        file_size: "",
        download_url: "",
        deleting: false,
        delete_done: false,
    };

    app.enumerate = (a) => {
        // This adds an _idx field to each element of the array.
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


    app.set_result = function (r) {
        // Sets the results after a server call.
        app.vue.file_name = r.data.file_name;
        app.vue.file_type = r.data.file_type;
        app.vue.file_date = r.data.file_date;
        app.vue.file_path = r.data.file_path;
        app.vue.file_size = r.data.file_size;
        app.vue.download_url = r.data.download_url;
    }

    app.upload_file = function (event) {
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

    // app.upload_complete = function (file_name, file_type) {
    //     app.vue.uploading = false;
    //     app.vue.upload_done = true;
    //     app.vue.uploaded_file = file_name;
    //     app.get_snps();
    // };

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

    app.computed = {
        file_info: app.file_info,
    };

    // This contains all the methods.
    app.methods = {
        // Complete as you see fit.
        upload_file: app.upload_file,
        upload_complete: app.upload_complete,
        get_snps: app.get_snps,
        retrieve_snps: app.retrieve_snps,
        delete_file: app.delete_file,
        download_file: app.download_file,
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

        app.get_snps();

    };

    // Call to the initializer.
    app.init();
};

// This takes the (empty) app object, and initializes it,
// putting all the code i
init(app);