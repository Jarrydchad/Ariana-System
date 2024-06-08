$(document).ready(function() {
    // Attach a listener to the input field
    $('#learnerSearch').on('input', function() {
        // Get the value from the input field
        var searchTerm = $(this).val();

        // Send an AJAX request to the server to fetch search results
        $.ajax({
            url: '/search',
            method: 'POST',
            data: { term: searchTerm },
            success: function(data) {
                $('#learnerSelect').html(data); // Assuming 'learnerSelect' is the ID of your select box
                $('#learnerSelect').show();
                if (searchTerm === '') {
                    $('#learnerSelect').empty();
                    // Optionally, add a default option
                }
            }
        });
    });
});
