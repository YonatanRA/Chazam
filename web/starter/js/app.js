const recorder = RecorderManager.create()

record.onclick = () => recorder.start()

setTimeout(() => {
  recorder
    .stop()
    .then(({ blob }) => uploadToCloudIdentifier(blob))
    .then(data => console.log(data))
}, 5000)