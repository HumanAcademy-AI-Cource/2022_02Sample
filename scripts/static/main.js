// rosbridgeと接続
var ros = new ROSLIB.Ros({ url: "ws://" + location.hostname + ":9000" });
// 圧縮画像を代入する変数を定義
var base64image;

// 接続時にログを出力
ros.on("connection", function () {
  console.log("websocket: connected");
});
// エラー時にログを出力
ros.on("error", function (error) {
  console.log("websocket error: ", error);
});
// 切断時にログを出力
ros.on("close", function () {
  console.log("websocket: closed");
});

// サブスクライブするトピックとメッセージ型を指定
var image_raw = new ROSLIB.Topic({
  ros: ros,
  name: "/usb_cam/image_raw/compressed",
  messageType: "sensor_msgs/CompressedImage",
});

const sceneRekognitionClient = new ROSLIB.Service({
  ros: ros,
  name: "/scene_rekognition",
  serviceType: "aws_demokit/SceneRekognition",
});

// サブスクライブした画像をブラウザ上に表示する
image_raw.subscribe(function (message) {
  base64image = "data:image/jpeg;base64," + message.data;
  document.getElementById("image").src = base64image;
});

var isPermitSound = false;
document.getElementById("permit_sound_button").onclick = () => {
  isPermitSound = true;
  document.getElementById("permit_sound_button").innerHTML = "音声再生を許可済";
  document.getElementById("permit_sound_button").className = "btn btn-outline-success btn-lg btn-block";
  document.getElementById("permit_sound_button").disabled = true;
  const audio = new Howl({ src: ["./static/silence.wav"], volume: 0 });
};

document.getElementById("scene_rekognition_button").onclick = () => {
  const request = new ROSLIB.ServiceRequest({});
  document.getElementById("scene_rekognition_button").disabled = true;
  sceneRekognitionClient.callService(request, (result) => {
    if (isPermitSound) {
      const audio = new Howl({
        src: ["./audio/" + result.audio_filename],
        preload: true, // 事前ロード
        volume: 1.0, // 音量(0.0〜1.0の範囲で指定)
        loop: false, // ループ再生するか
        autoplay: true, // 自動再生するか
      });

      audio.on("end", function () {
        document.getElementById("scene_rekognition_button").disabled = false;
      });
    } else {
      document.getElementById("scene_rekognition_button").disabled = false;
    }

    const base64image2 = "data:image/jpeg;base64," + result.detect_image.data;
    document.getElementById("result_image").src = base64image2;

    document.getElementById("data_area").innerHTML = "";
    const table = document.createElement("table");
    table.className = "table table-striped";
    const tr = document.createElement("tr");
    const th1 = document.createElement("th");
    th1.textContent = "ラベル";
    const th2 = document.createElement("th");
    th2.textContent = "信頼度";
    tr.appendChild(th1);
    tr.appendChild(th2);
    table.appendChild(tr);
    for (let i = 0; i < result.labels.length; i++) {
      const tr = document.createElement("tr");
      for (let j = 0; j < 1; j++) {
        const td1 = document.createElement("td");
        td1.textContent = result.labels[i];
        tr.appendChild(td1);
        const td2 = document.createElement("td");
        td2.textContent = result.confidence[i].toFixed(1) + "%";
        tr.appendChild(td2);
      }
      table.appendChild(tr);
    }
    document.getElementById("data_area").appendChild(table);
  });
};
