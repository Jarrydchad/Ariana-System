//function fetchStudents() {
//  var schoolSelect = document.getElementById("schoolSelect");
//  var selectedSchool = schoolSelect.value;
//
//  // Show loader
//  document.getElementById("loader").style.display = "block";
//
//  // Simulate fetching data with setTimeout
//  setTimeout(function() {
//    // Hide loader
//    document.getElementById("loader").style.display = "none";
//
//    // Show student list
//    document.getElementById("studentList").style.display = "block";
//
//    // Populate student select options based on selected school
//    var studentSelect = document.getElementById("studentSelect");
//    studentSelect.innerHTML = "";
//
//    if (selectedSchool === "astra") {
//      var students = ["John Doe", "Jane Smith", "Mike Johnson"];
//    } else if (selectedSchool === "gelvandale") {
//      var students = ["Alice Brown", "Bob White", "Emily Green"];
//    } else if (selectedSchool === "fernwood") {
//      var students = ["Chris Taylor", "David Clark", "Sophie Evans"];
//    } else if (selectedSchool === "triomf") {
//      var students = ["Tom Wilson", "Sarah King", "Olivia Harris"];
//    } else {
//      var students = [];
//    }
//
//    students.forEach(function(student) {
//      var option = document.createElement("option");
//      option.text = student;
//      studentSelect.add(option);
//    });
//  }, 2000); // Simulate 2 seconds delay for fetching data
//}
//
//function proceedToPayment() {
//  var studentSelect = document.getElementById("studentSelect");
//  var selectedStudent = studentSelect.value;
//
//  // Redirect to payment page with selected student
//  if (selectedStudent) {
//    window.location.href = "payment.html?student=" + encodeURIComponent(selectedStudent);
//  } else {
//    alert("Please select a student.");
//  }
//}

function autocomplete() {
  var searchInput = document.getElementById("searchInput");
  var autocompleteResults = document.getElementById("autocompleteResults");
  var search_term = searchInput.value;

  if (search_term.length < 2) {
    autocompleteResults.innerHTML = "";
    return;
  }

  var xhr = new XMLHttpRequest();
  xhr.open("GET", "/autocomplete?term=" + search_term, true);
  xhr.onreadystatechange = function() {
    if (xhr.readyState == 4 && xhr.status == 200) {
      var data = JSON.parse(xhr.responseText);
      var html = "";
      data.forEach(function(item) {
        html += "<div>" + item.name + " (" + item.type + ")</div>";
      });
      autocompleteResults.innerHTML = html;
    }
  };
  xhr.send();
}

