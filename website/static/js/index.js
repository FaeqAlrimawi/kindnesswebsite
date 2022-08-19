

function delete_AoK(aokId){
    fetch('/delete-AoK', {
        method: 'POST',
        body: JSON.stringify({aokId: aokId})
    }).then((_res) => {
        window.location.href="/edit";
    });
}

function delete_media(mediaID) {
    fetch('/delete-media', {
        method: 'POST',
        body: JSON.stringify({mediaID: mediaID})
    }).then((_res) => {
        window.location.href="/media";
    });
}