(function (root, factory) {
    if (typeof define === 'function' && define.amd) {
        define([], factory);
    } else {
        root.PdfThumbnail = factory();
    }
}(this, function () {
    return function PdfThumbnail(pdf, format, quality, size) {

        if (typeof PDFJS === 'undefined') {
            throw Error("pdf.js is not loaded. Please include it before pdfThumbnails.js.");
        }
        PDFJS.disableWorker = true;

        // if (typeof image === 'string') {
            // image = document.getElementById(image);
        // }

        format = format || 'jpeg';
        quality = quality || 0.92;

        if (!pdf || (format !== 'png' && format !== 'jpeg')) {
            return false;
        }

        var canvas = document.createElement("CANVAS");

        size = (size == undefined) ? 100 : size;

        var ratio = image.width / image.height;
        canvas.width = size;
        canvas.height = size;

        var delta = image.width - image.height;
        var x0 = 0, y0 = 0;
        var width = image.width, height = image.height;
        if(delta>0){
            x0 = delta / 2;
            width = height;
        }else if (delta <0){
            y0 = -(delta / 2);
            height = width;
        }
        console.log(x0, y0);
        console.log(height, width);

        var context = canvas.getContext('2d')

        var source = { x: x0, y: y0, width: width, height: height };
        var dest = { x: 0, y: 0, width: size, height: size };

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
