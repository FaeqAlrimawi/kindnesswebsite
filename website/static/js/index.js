
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


function delete_AoK(aokId){
    fetch('/delete-AoK', {
        method: 'POST',
        body: JSON.stringify({aokId: aokId})
    }).then((_res) => {
        window.location.href="/edit";
    });
}
