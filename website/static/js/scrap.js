
var gridOptions = null;
var oneClickInerval = null;
var clicked = false;


function headerHeightSetter() {
  var padding = 20;
  var height = headerHeightGetter() + padding;
  gridOptions.api.setHeaderHeight(height);
}

function headerHeightGetter() {
  var columnHeaderTexts = [
      ...document.querySelectorAll('.ag-header-cell-text'),
  ];
  var clientHeights = columnHeaderTexts.map(
      headerText => headerText.clientHeight
  );
  var tallestHeaderTextHeight = Math.max(...clientHeights);

  return tallestHeaderTextHeight;
}



function createActsGrid() {
    // console.log("create grid");
  // Grid Options are properties passed to the grid
   gridOptions = {

    // each entry here represents one column
    columnDefs: [
      { field: "id", hide:true }, 
      {
        headerName: "#",
        valueGetter: "node.rowIndex + 1", maxWidth: 90, minWidth:80,   checkboxSelection: true
      },
      { field: "text",  headerName:"Text", editable: true, minWidth: 500},
      { field: "prob_aok", headerName:"AoK%", maxWidth: 120, valueFormatter: params => params.data.prob_aok.toFixed(2)}
      
    ],

    
    onFirstDataRendered: headerHeightSetter,
    onColumnResized: headerHeightSetter,

    onGridSizeChanged: () => {
      gridOptions.api.sizeColumnsToFit();
  } ,    

    // default col def properties get applied to all columns
    defaultColDef: {sortable: true, filter: true,  wrapText: true,  flex: 1,
    autoHeight: true, resizable: true, cellClass: 'locked-col',  lockPosition: 'left'},
    
    // enableRangeSelection: true,
    // fillHandleDirection: 'x',
    // enableFillHandle: true,
    
    rowSelection: 'multiple', // allow rows to be selected
    animateRows: true, // have rows animate to new positions when sorted

    pagination: true,
    paginationAutoPageSize: true,
    // example event handler
    // onCellClicked: params => {
    //   console.log('cell was clicked', params)
    // }
    onCellValueChanged: e => {
      let newAct = e.newValue;
      let oldAct = e.oldValue;

      updateAct(oldAct, newAct);
    } 

    
  };

  // get div to host the grid
  const eGridDiv = document.getElementById("myGrid");
  // new grid instance, passing in the hosting DIV and Grid Options
  new agGrid.Grid(eGridDiv, gridOptions);

  // gridOptions.api.hideOverlay();
  // Fetch data from server
  // fetch("/api/actdata")
  // .then(response => response.json())
  // .then(data => {
  //   // load fetched data into grid
  //   // console.log(data[0]);
  //   gridOptions.api.setRowData(data);
  // });
}


function add_Aoks() {

  const selectedNodes = gridOptions.api.getSelectedNodes();
  const selectedRows = gridOptions.api.getSelectedRows();

    
  if (selectedNodes.length == 0 ) {
    let msg = "<span class=\"w3-red w3-round\" style=\"font-size: 1.2em;\"> "+
    "&nbsp;&nbsp; Please select acts from the table &nbsp;&nbsp; </span>";
    showActOpMsg(msg);
    return;
  }

  var selectedData = selectedNodes.map( function(node) { return node.data });

  var mapResult = new Map();


  for(let i=0;i<selectedData.length;i++) {
    actID = selectedData[i].id;

    message = add_AoK(actID);

    if (message == "error"){
      mapResult.set(actID, message);
    } else {
      //delet from table
      gridOptions.api.applyTransaction({remove: [selectedRows[i]]});
    }
    
  }

  if(mapResult.size == 0) {
   showActOpMsg("<span style='color: green;'>"+
    "Successfully added <b>"+ selectedData.length+"</b> act(s)</span>");
  
    // gridOptions.api.applyTransaction({remove: selectedNodes});
  } else {
    showActOpMsg("<span style='color: red;'>"+
    "Could not add "+ mapResult.length+" acts</span>");
  }


}

function add_AoK(actID){

  //  if (btn) {
  //   span = btn.childNodes[0]
  //  }

   // var act = $('#td-'+row).text();
    // console.log("row: "+row +" act: " + act);
    
    fetch('/add-AoK', {
        method: 'POST',
        body: JSON.stringify({actID: actID}),
        cache: "no-cache",
        headers: new Headers({
            "content-type": "application/json"
        })
    }).then((response) => {

        return response.json();        
    }).then((data) => {
        
        message = data['message'];

       return message; 
    }

    ).catch(err => console.log(err));
}



function checkURL (abc) {
    var string = abc.value;
    if (!~string.indexOf("http")) {
      string = "http://" + string;
    }
    abc.value = string;
    return abc
  }


// function getContactFormData(form) {
//     // creates a FormData object and adds chips text
//     var formData = new FormData(document.getElementById(form));
// //    for (var [key, value] of formData.entries()) { console.log('formData', key, value);}
//     return formData
// }




function scrap(websiteURL) {

    // console.log("@@@ " + websiteURL);
    $('#websiteURL').val(websiteURL);
 
    $('#scrapForm').trigger('submit');
}

// function getContactFormData(form) {
//   // creates a FormData object and adds chips text
//   var formData = new FormData(document.getElementById(form));
// //    for (var [key, value] of formData.entries()) { console.log('formData', key, value);}
//   return formData
// }


function fillActsGrid(website) {
   

  if(gridOptions == null) {
      createActsGrid();
  }

  fetch("/api/actdata", {
    method: 'POST',
    body: JSON.stringify({operation: 'fetch-all', data:website}),
    cache: "no-cache",
    headers: new Headers({
        "content-type": "application/json"
    })
})
.then(response => response.json())
.then(data => {
  // load fetched data into grid
  // console.log(data[0]);
  gridOptions.api.setRowData(data);
});

}


function updateAct(oldAct, newAct){

  if(newAct == null || newAct == "" ) {
    return;
  }  

  fetch("/api/actdata", {
    method: 'POST',
    body: JSON.stringify({operation:'updateAct', data: [oldAct, newAct]}),
    cache: "no-cache",
    headers: new Headers({
        "content-type": "application/json"
    })
})
.then(response => response.json())
.then(data => {
  // load fetched data into grid
  // console.log(data[0]);
  // gridOptions.api.setRowData(data);
  // if(data['response'] == "success") {
  // console.log("updated successfully")
  // }
});

}

function deleteAoKs() {

  const selectedNodes = gridOptions.api.getSelectedNodes();
  const selectedRows = gridOptions.api.getSelectedRows();

    //label
    // var lbl = document.getElementById("lbl-add");
    // lbl.innerHTML = "";
  
    
  if (selectedNodes.length == 0 ) {
   showActOpMsg("<span style='color: red;'>"+
    "Please select acts from the table");
    return;
  }

  var selectedData = selectedNodes.map( function(node) { return node.data });

  var mapResult = new Map();


  for(let i=0;i<selectedData.length;i++) {
    actID = selectedData[i].id;

    message = deleteAoK(actID);

    if (message == "error"){
      mapResult.set(actID, message);
    } else {
      //delet from table
      gridOptions.api.applyTransaction({remove: [selectedRows[i]]});
    }
    
  }

  if(mapResult.size == 0) {
    showActOpMsg("<span style='color: green;'>"+
    "Successfully deleted <b>"+ selectedData.length+"</b> act(s)</span>");
    
    // gridOptions.api.applyTransaction({remove: selectedNodes});
  } else {
    showActOpMsg("<span style='color: red;'>"+
    "Could not delete "+ mapResult.length+" acts</span>");
  }

}

function deleteAoK(id) {

  console.log("deleting " + id);

  if(id == null ) {
    return;
  }  

  fetch("/api/actdata", {
    method: 'POST',
    body: JSON.stringify({operation:'removeAct', data:id}),
    cache: "no-cache",
    headers: new Headers({
        "content-type": "application/json"
    })
})
.then(response => response.json())
.then(data => {
  // load fetched data into grid
  // console.log(data[0]);
  // gridOptions.api.setRowData(data);
  return data['response']
  
 
});

}

function notifyDoubleClick() {


  if (!clicked) {
    // if(oneClickInerval == null) {
      oneClickInerval = setInterval(showDeleteAlert, 600)
      clicked = true;
    // }
    
    // setTimeout(oneClickInerval);
     
  } else {
    clearInterval(oneClickInerval);
    clicked = false;
  }
 

 
    
  // lbl.innerHTML = "<span class=\"w3-orange w3-round\" style=\"font-size: 1.2em;\"> "+
  // "<b> &nbsp;&nbsp; Double Click</b> to delete &nbsp;&nbsp; </span>";

  // setTimeout(function(){
  //   lbl.innerHTML="";
  //   },2000);

  
}


function showDeleteAlert() {
  
  var lbl = document.getElementById("lbl-add");

  showActOpMsg("<span class=\"w3-orange w3-round\" style=\"font-size: 1.2em;\"> "+
  "<b> &nbsp;&nbsp; Double Click</b> to delete &nbsp;&nbsp; </span>");
 
   clicked = false;

   clearInterval(oneClickInerval);

   setTimeout(function(){
    lbl.innerHTML="";
    },2000);

}

function showActOpMsg(msg) {

  var lbl = document.getElementById("lbl-add");

  lbl.innerHTML = msg;

  setTimeout(function(){
    lbl.innerHTML="";
    },2000);

}