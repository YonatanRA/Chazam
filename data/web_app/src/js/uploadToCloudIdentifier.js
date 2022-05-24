const UPLOAD_IDENTIFIER_API = "http://yon.pythonanywhere.com/";

const uploadToCloudIdentifier = async (blob) => {
  console.log("Uploading...");
  let formData = new FormData();
  formData.append("blob", blob);

  const res = await axios.post(
    `${UPLOAD_IDENTIFIER_API}`,
    formData
  );
  if (res.status == 200) {
    console.log("Done!");
    const data = res.data;
    console.log(data);
    return data;
  } else {
    console.log("Failed");
    throw new Error("Failed to upload to cloud");
  }
};
