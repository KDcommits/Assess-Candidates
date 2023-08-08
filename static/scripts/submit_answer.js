function submitAnswers() {
    var answers = {
        {% for row in qna_data %}
        q{{loop.index}}: document.getElementById('q{{loop.index}}_answer').value,
        {% endfor %}
    };

    // Send the answers to the Flask backend using Fetch API
    fetch('/submit_answers', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify(answers),
    })
    .then(response => response.json())
    .then(data => {
        // Handle the response from the backend (if needed)
        console.log(data);
    })
    .catch(error => {
        console.error('Error:', error);
    });
}