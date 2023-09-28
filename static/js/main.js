function updateProgressBar(progress){
    progress = Math.round(progress)
    let elemProgressBar = document.querySelector('.progress-bar');
    elemProgressBar.style.width = `${progress}%`;
    elemProgressBar.innerText = `${progress}%`;   
}

async function startAnalysis(league_id, week) {

    let progress = 0;
    updateProgressBar(progress);
    
    await fetch(`/${league_id}/${week}/start`, { method: 'GET' });
    const resp = await (await fetch(`/${league_id}/teams`, { method: 'GET' })).json();

    let team_num = resp.team_ids.length;
    let step = 90 / team_num;  // make the progress bar shows 60% after retriveing data from yahoo
    for (let i = 0; i < team_num; i++) {
        let team_id = resp.team_ids[i];
        await fetch(`/stat/${league_id}/${week}/${team_id}`, { method: 'GET' })
        progress += step;
        updateProgressBar(progress);
    }
    
    await fetch(`/${league_id}/${week}/analyze`, { method: 'GET' })
    updateProgressBar(100);
    window.location.href = `/${league_id}/${week}`;
}


const analyisButtons = document.querySelectorAll('.btn-analyis');
for (let i = 0; i < analyisButtons.length; i++) {
    analyisButtons[i].addEventListener("click", (e) => {
        // show the progress bar
        let progressBar = document.querySelector('.progress');
        progressBar.classList.remove('d-none');  

        // console.log(e.target);
        league_id = e.target.dataset.leagueId
        week = e.target.dataset.week
        startAnalysis(league_id, week)
    });
}
