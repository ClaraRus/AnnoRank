    function limitSelection(checkbox, max) {
        var checkboxes = document.querySelectorAll('input[type="checkbox"]');
        var selectedCheckboxes = document.querySelectorAll('input[type="checkbox"]:checked');

        if (selectedCheckboxes.length > max) {
            checkbox.checked = false;
            alert("You can only select up to  " + max + " docs.");
        }
    }

    function toggleCheckbox(id_1, id_2) {
        var checkbox_1 = document.getElementById(id_1);
        var checkbox_2 = document.getElementById(id_2);

        // Toggle the checked state of the clicked checkbox
        if (checkbox_2.checked){
        checkbox_2.checked = false;
        }


        // Uncheck the other checkbox
        checkbox_1.checked = true;
}
