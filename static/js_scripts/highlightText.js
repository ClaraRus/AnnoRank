function highlightText(){
// Get the query text and split it into an array of tokens
var query_text = document.getElementById('query_info').textContent.replace(/\s+/g, ' ').trim().split(' ');

// Loop through each row of the table
var tr_list = document.getElementsByTagName('tr');
for (var i = 0; i < tr_list.length; i++) {
    // Get all table cells within the row
    var td_list = tr_list[i].getElementsByTagName('td');

    // Loop through each table cell
    for (var j = 0; j < td_list.length; j++) {
        // Get the text content of the table cell

        if (td_list[j].querySelector('button') || td_list[j].querySelector('input[type="checkbox"]')) {
            continue; // Skip processing if the cell contains a button
        }

        var cell_text = td_list[j].textContent;
        console.log(cell_text)
        // Loop through each token in the query text
        for (var k = 0; k < query_text.length; k++) {
            var query_token = query_text[k].replace(",", "").trim();
            var regex = new RegExp('\\b' + query_token + '\\b', 'g'); // Match whole word only

            // Replace the matched tokens with the same token wrapped in a <span> element with bold styling
            cell_text = cell_text.replace(regex, '<span style="font-weight: bold;">$&</span>');
        }

        // Update the content of the table cell with the modified text
        td_list[j].innerHTML = cell_text;
    }
}

}

