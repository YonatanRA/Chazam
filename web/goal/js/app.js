const recorder = RecorderManager.create()

record.onclick = startListening

function startListening() {
  document.body.classList.add('listening')
  statusText.textContent = 'Escuchando...'
  recorder.start()
  setTimeout(() => stopListening(), 3000)
}

function stopListening() {
  document.body.classList.remove('listening')
  statusText.textContent = 'Obteniendo resultados...'
  recorder
    .stop()
    .then(({ blob }) => uploadToCloudIdentifier(blob))
    .then(data => {
      showResult(data)
    })
}

function showResult(data) {
  artistName.innerText = data.artist
  trackName.innerText = data.song
  albumCover.src = data.cover
  document.body.classList.add('listened')
}

restart.onclick = () => document.body.className = ''