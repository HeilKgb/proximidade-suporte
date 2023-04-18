(function (root, factory) {
    if (typeof define === 'function' && define.amd) {
        define([], factory);
    } else {
        root.captureVideoFrame = factory();
    }
}(this, function () {
    return function captureVideoFrame(video, format, quality, size) {
        if (typeof video === 'string') {
            video = document.getElementById(video);
        }

        format = format || 'jpeg';
        quality = quality || 0.92;

        if (!video || (format !== 'png' && format !== 'jpeg')) {
            return false;
        }

        var canvas = document.createElement("CANVAS");

        size = (size == undefined) ? 100 : size;

        var ratio = video.videoWidth / video.videoHeight;
        canvas.width = size;
        canvas.height = size;

        var delta = video.videoWidth - video.videoHeight;
        var x0 = 0, y0 = 0;
        var width = video.videoWidth, height = video.videoHeight;
        if(delta>0){
            x0 = delta / 2;
            width = height;
        }else if (delta <0){
            y0 = -(delta / 2);
            height = width;
        }

        var context = canvas.getContext('2d')

        var source = { x: x0, y: y0, width: width, height: height };
        var dest = { x: 0, y: 0, width: size, height: size };

        context.drawImage(video,
            source.x, source.y,
            source.width, source.height,
            dest.x, dest.y,
            dest.width, dest.height);

        // canvas.width = video.videoWidth;
        // canvas.height = video.videoHeight;

        // var context = canvas.getContext('2d')
        // context.drawImage(video, 0, 0);

        var dataUri = canvas.toDataURL('image/' + format, quality);
        var data = dataUri.split(',')[1];
        var mimeType = dataUri.split(';')[0].slice(5)

        var bytes = window.atob(data);
        var buf = new ArrayBuffer(bytes.length);
        var arr = new Uint8Array(buf);

        for (var i = 0; i < bytes.length; i++) {
            arr[i] = bytes.charCodeAt(i);
        }

        var blob = new Blob([ arr ], { type: mimeType });
        return { blob: blob, dataUri: dataUri, format: format };
    };
}));
