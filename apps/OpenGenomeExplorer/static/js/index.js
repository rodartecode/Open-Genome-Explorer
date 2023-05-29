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

    // This contains all the methods.
    app.methods = {
        // Complete as you see fit.
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

        app.get_snps();

    };

    // Call to the initializer.
    app.init();
};

// This takes the (empty) app object, and initializes it,
// putting all the code i
init(app);