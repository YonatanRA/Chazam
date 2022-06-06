const log = (e, data) =>
  (window.log.innerHTML += "\n" + e + " " + (data || ""));

const appendToList = (url) => {
  const li = document.createElement("li");
  const au = document.createElement("audio");
  const hf = document.createElement("a");

  // Configure audio element
  au.controls = true;
  au.src = url;
  hf.href = url;
  hf.download = new Date().toISOString() + ".wav";
  hf.innerHTML = hf.download;

  // Append to dom
  li.appendChild(au);
  li.appendChild(hf);
  window.recordingslist.appendChild(li);
};

const recorder = RecorderManager.create();

recordButton.disabled = false;
stopButton.disabled = true;

recordButton.onclick = () => {
  recorder
    .start()
    .then(() => {
      log("Started recording");
      recordButton.disabled = true;
      stopButton.disabled = false;
    })
    .catch(log);
};

stopButton.onclick = () => {
  recorder
    .stop()
    .then(({ url, blob }) => {
      log(`Done! stopped recording. ${url}`);
      recordButton.disabled = false;
      stopButton.disabled = true;
      appendToList(url);
      log(`Identifying song....`);
      return uploadToCloudIdentifier(blob);
    })
    .then((data) => {
      log(`Identified Song -> "${data}"`);
    })
    .catch(log);
};
