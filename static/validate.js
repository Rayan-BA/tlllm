
const validate = () => {
    const form = document.forms["rgstr-form"]
    const form_el = form.elements
    const allowedUsernames = /^[a-zA-Z0-9\_\.]+$/
    console.log(form_el);

    if (form_el["username"].value === "") {
        alert("Username required")
    } else if (form_el["password"].value === "" && form_el["confirm_password"].value === "") {
        alert("Password required")
    } else if (!allowedUsernames.test(form_el["username"].value)) {
        alert("Only letters, numbers, dots and underscores allowed")
    } else if (form_el["password"].value !== form_el["confirm_password"].value) {
        alert("Passwords do not match")
    } else {
        form.submit()
    }
}

const showPass = () => {
    if (el.type === "password") {
        x.type = "text";
    } else {
        el.type = "password";
    }
}