class RecorderManager {
  constructor() {
    this.isRecording = false;
  }

  getRecorder(ready) {
    return new Promise((resolve, reject) => {
      if (!this.input || !this.recorder) {
        navigator.getUserMedia(
          { audio: true },
          (stream) => {
            const audio_context = new AudioContext();
            this.input = audio_context.createMediaStreamSource(stream);
            this.recorder = new Recorder(this.input, { numChannels: 1 });
            console.log("Media stream created. Recorder initialised.");
            resolve(this.recorder);
          },
          reject
        );
      } else {
        console.log("Reusing Recorder context");
        resolve(this.recorder);
      }
    });
  }

  async start() {
    if (!this.isRecording) {
      const recorder = await this.getRecorder();
      recorder.record();
      this.isRecording = true;
    } else {
      throw new Error("Already recording");
    }
  }

  async stop() {
    if (this.isRecording) {
      const recorder = await this.getRecorder();
      recorder.stop();
      const { url, blob } = await this.createDownloadLink();
      this.isRecording = false;
      return { url, blob };
    } else {
      throw new Error("Not Recording");
    }
  }

  createDownloadLink() {
    // create WAV download link using audio data blob
    return new Promise((resolve, reject) => {
      console.log("Generating record data...");
      this.recorder.exportWAV((blob) => {
        var url = URL.createObjectURL(blob);
        this.recorder.clear();
        resolve({
          url,
          blob,
        });
      });
    });
  }
}

RecorderManager.create = () => {
  let instance = new RecorderManager();
  return instance;
};
