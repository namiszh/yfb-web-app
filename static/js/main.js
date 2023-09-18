function startAnalysis(elem, league_id, week) {
    fetch(`/${league_id}/${week}/polling`, { method: 'GET' })
    .then(resp => resp.json())
    .then(result => {
 
        if (result.status !== 'finished') {
            progress = result.progress
            elem.textContent = `${progress}%...`;
            setTimeout(function() {
                startAnalysis(elem, league_id, week);
            } , 1000);
        } else {
            window.location.href = `./${league_id}/${week}`;
        }
    })
    .catch(errorMsg => { console.log(errorMsg); });
}


const analyisButtons = document.querySelectorAll('.btn-analyis');
for (let i = 0; i < analyisButtons.length; i++) {
    analyisButtons[i].addEventListener("click", (e) => {
        e.target.textContent = 'Analyzing...';
        league_id = e.target.dataset.leagueId
        week = e.target.dataset.week
        startAnalysis(e.target, league_id, week)
    });
}
