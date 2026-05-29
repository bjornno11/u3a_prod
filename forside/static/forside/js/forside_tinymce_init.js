document.addEventListener("DOMContentLoaded", function () {
  if (typeof tinymce === "undefined") {
    return;
  }

  tinymce.init({
    selector:
      "textarea#id_left_column, textarea#id_center_column, textarea#id_right_column",

    height: 350,
    menubar: false,

    plugins: "image link lists code",

    // "blocks" gir deg H1–H6-menyen
    toolbar:
      "undo redo | blocks | bold italic underline | image | bullist numlist | link | code",

    branding: false,
    promotion: false,

    // TinyMCE 7 forventer at vi returnerer en Promise her
    images_upload_handler: function (blobInfo, progress) {
      return new Promise(function (resolve, reject) {
        var xhr = new XMLHttpRequest();
        xhr.withCredentials = false;
        xhr.open("POST", "/upload-image/");

        xhr.upload.onprogress = function (e) {
          if (e.lengthComputable) {
            var percent = (e.loaded / e.total) * 100;
            progress(percent);
          }
        };

        xhr.onload = function () {
          if (xhr.status !== 200) {
            reject("HTTP Error: " + xhr.status);
            return;
          }

          var json;
          try {
            json = JSON.parse(xhr.responseText);
          } catch (e) {
            reject("Invalid JSON: " + xhr.responseText);
            return;
          }

          if (!json || typeof json.location !== "string") {
            reject("Invalid JSON: " + xhr.responseText);
            return;
          }

          // Dette er URL-en TinyMCE setter inn i editoren
          resolve(json.location);
        };

        xhr.onerror = function () {
          reject("Image upload failed due to a XHR Transport error.");
        };

        var formData = new FormData();
        formData.append("file", blobInfo.blob(), blobInfo.filename());
        xhr.send(formData);
      });
    },
  });
});
