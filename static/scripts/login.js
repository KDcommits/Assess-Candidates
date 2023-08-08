document.getElementById("login-form").addEventListener("submit", function (event) {
    event.preventDefault();
    const form = event.target;
    const data = new FormData(form);
    const requestData = {
        method: "POST",
        body: data,
    };

    fetch("/login", requestData)
        .then((response) => response.json())
        .then((data) => {
            if (data.success) {
                window.location.href = "/test_instructions"; 
            } else {
                alert("Invalid credentials. Please try again.");
            }
        })
        .catch((error) => {
            console.error("Error:", error);
        });
});