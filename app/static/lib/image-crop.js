(function (root, factory) {
    if (typeof define === 'function' && define.amd) {
        define([], factory);
    } else {
        root.ImageCrop = factory();
    }
}(this, function () {
    return function ImageCrop(image, format, quality, size) {
        if (typeof image === 'string') {
            image = document.getElementById(image);
        }

        format = format || 'jpeg';
        quality = quality || 0.92;

        if (!image || (format !== 'png' && format !== 'jpeg')) {
            return false;
        }

        var canvas = document.createElement("CANVAS");
        size = (size == undefined) ? 100 : size;

        var ratio = image.width / image.height;

        var x0 = 0, y0 = 0;

        canvas.width = size;
        canvas.height = size;
        var source = { x: x0, y: y0, width: image.width, height: image.height };
        var height = size;
        var width = size*(image.width / image.height);
        var y = 0;
        var x = (size - width) / 2;
        if(image.width > image.height){
            width = size;
            height = size*(image.height / image.width);
            x = 0;
            y = (size - height) / 2;
        }
        var dest = { x: x, y: y, width: width, height: height };

        var context = canvas.getContext('2d')
        context.drawImage(image,
            source.x, source.y,
            source.width, source.height,
            dest.x, dest.y,
            dest.width, dest.height);

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
