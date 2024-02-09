 console.log("submit_form")
 function submit_form(items) {
    console.log("submit")
      // Get values from the form
      var done_mandatory = true
      var form_value_dict = {}
      for (var item in items) {
            var element_value = document.getElementById(items[item].field).value;
            form_value_dict[items[item].field] = element_value;
            if (items[item].mandatory) {


                if (element_value === '') {
                    done_mandatory = false;
                }
            }
        }
      if (done_mandatory) {
      // Use jQuery AJAX to send data to the Flask app
      $.ajax({
        type: "POST",
        url: "/form_submit",
        contentType: "application/json;charset=UTF-8",
        data: JSON.stringify({
            form_results: form_value_dict,
        }),
        success: function(response) {
          console.log("Success:", response);

          // Redirect to the next page after successful data storage
          window.location.href = "/stop_experiment";
        },
        error: function(error) {
          console.log("Error:", error);
        }
      });
      } else {
        // Display a message to the user if less than three docs are selected
        alert("Please select a value for both gender and nationality!");
      }


    }

