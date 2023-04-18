/* jshint unused:vars */
'use strict';

angular.module('attach-files.controller', [])

.controller('AttachFilesCtrl', ['$scope', '$timeout', '$q', '$ModalPage', '$uibModalInstance', 'attachments',
	function($scope, $timeout, $q, $ModalPage, $uibModalInstance, attachments){

	$scope.attachments = attachments;
	$scope.dataloading = false;
	$scope.title = $scope.actionType=='attach' ? 'Adicionar Arquivos': 'Enviar Arquivos';

	$scope.Cancel = function(){
		$uibModalInstance.dismiss("close");
	};

	$scope.Submit = function (form){
		if(_.some($scope.attachments, {comment:''})) {
			var msg = 'Adicione uma descrição ao arquivo.'
			var count = _.filter($scope.attachments,{comment:''}).length;
			if (count > 1)
				msg = 'Adicione uma descrição para cada arquivo.';
			$ModalPage({
				data: {
					title: 'Aviso',
					message: msg,
					msg_close: 'Fechar'
				}
			},{
				templateUrl: 'Warning.tpl.html',
				controller: 'WarningCtrl',
				size: 'sm',
				windowClass: 'dlg-warning',
				backdrop: 'static',
				animation: true
			})
			.then(function(response) {}, function (error) {});
		}
		else{
			$uibModalInstance.close({attachments: $scope.attachments });
		}
	};

	$scope.remove = function(attachment){
		_.remove($scope.attachments, attachment);
		Reindex();
		if($scope.attachments.length>0)
			$scope.SetActive($scope.attachments[0]);
	};

	function Reindex() {
		_.forEach($scope.attachments, function(attachment, index){
			attachment.id = index;
		});
	}

	var SetFiles = function(file, id){
		var deferred = $q.defer();
		var tipo = file.type.split("/")[0];
		var thumb_name = file.name.replace(/\.[^/.]+$/, "") + '.thm';
		var extension = file.name.replace(/^.*?\.([a-zA-Z0-9]+)$/, "$1").toLowerCase();
		if(tipo == "video"){
			var video_url = URL.createObjectURL(file);
			var video = document.createElement("video"),
				source = document.createElement("source");
			source.src = video_url;
			video.appendChild(source);
			video.onloadeddata = function() {
				var frame = captureVideoFrame(video, 'png');
				var attachment = {
					id: id,
					file: file,
					type: tipo,
					extension: extension,
					thumbnail: {
						dataUri: frame.dataUri,
						blob: frame.blob,
						filename: thumb_name
					},
					comment: ''
				};
				source.src = '';
				deferred.resolve(attachment);
			};
			video.load();
		}
		else if(tipo == "image"){
			var reader = new FileReader();
			var image = document.createElement("IMG");
			reader.onload = function(e) {
				image.src = e.target.result;
			}
			image.onload = function(){
				var frame = ImageCrop(image, 'png');
				var attachment = {
					id: id,
					file: file,
					type: tipo,
					extension: extension,
					thumbnail: {
						dataUri: frame.dataUri,
						blob: frame.blob,
						filename: thumb_name
					},
					comment: ''
				};
				image.src = '';
				deferred.resolve(attachment);
			}
			reader.readAsDataURL(file);
		}else if(tipo == "audio"){
			var attachment = {
				id: id,
				file: file,
				type: tipo,
				extension: extension,
				src: "/static/icons/audio-player.ico",
				comment: ''
			};
			deferred.resolve(attachment);
		}
		else if(tipo == 'application'){
			var subtype = file.type.split("/")[1];
			if(subtype == 'pdf'){
				var reader = new FileReader();
				var imgHeight = 300;
				var imgWidth = imgHeight * 210/297;
				reader.onload = function(e) {
					PDFJS.getDocument(e.currentTarget.result).then(function (pdf) {
						pdf.getPage(1).then(function (page) {
							var canvas = document.createElement("canvas");
							var viewport = page.getViewport(1.0);
							var context = canvas.getContext('2d');
							if (imgWidth) {
								viewport = page.getViewport(imgWidth / viewport.width);
							} else if (imgHeight) {
								viewport = page.getViewport(imgHeight / viewport.height);
							}
							canvas.height = viewport.height;
							canvas.width = viewport.width;
							page.render({
								canvasContext: context,
								viewport: viewport
							}).then(function () {
								var dataUri = canvas.toDataURL('image/' + 'jpeg', '0,92');
								var data = dataUri.split(',')[1];
								var mimeType = dataUri.split(';')[0].slice(5)
								var bytes = window.atob(data);
								var buf = new ArrayBuffer(bytes.length);
								var arr = new Uint8Array(buf);
								for (var i = 0; i < bytes.length; i++) {
									arr[i] = bytes.charCodeAt(i);
								}
								var blob = new Blob([ arr ], { type: mimeType });

								var attachment = {
									id: id,
									file: file,
									type: tipo,
									subtype: subtype,
									extension: extension,
									thumbnail: {
										dataUri: dataUri,
										blob: blob,
										filename: thumb_name
									},
									comment: ''
								};
								deferred.resolve(attachment);
							});
						}).catch(function() {
							deferred.reject();
							console.log("pdfThumbnails error: could not open page 1 of document " + filePath + ". Not a pdf ?");
						});
					}).catch(function() {
						deferred.reject();
						console.log("pdfThumbnails error: could not find or open document " + filePath + ". Not a pdf ?");
					});
				};
				reader.readAsArrayBuffer(file);
			}
			else {
				var subt = '';
				var src = '';
				if(subtype == 'msword' || subtype == 'vnd.openxmlformats-officedocument.wordprocessingml.document'){
					subt = 'msword';
					src = 'static/images/msword.png';
				}
				else if(subtype == 'vnd.ms-excel' || subtype == 'vnd.openxmlformats-officedocument.spreadsheetml.sheet'){
					subt = 'msexcel';
					src = 'static/images/msexcel.png';
				}
				else if(subtype == 'vnd.ms-powerpoint' || subtype == 'vnd.openxmlformats-officedocument.presentationml.presentation'){
					subt = 'msppt';
					src = 'static/images/mspowerpoint.png';
				}
				else if(subtype == 'json'){
					subt = 'json';
					src = 'static/images/json.png';
				}

				var attachment = {
					id: id,
					file: file,
					type: tipo,
					subtype: subt,
					src: src,
					extension: extension,
					comment: ''
				};
				deferred.resolve(attachment);
			}
		}
		else if(tipo == 'text'){
			var subt = 'text';
			var src = '';
			var attachment = {
				id: id,
				file: file,
				type: tipo,
				subtype: subt,
				src: src,
				extension: extension,
				comment: ''
			};
			deferred.resolve(attachment);
		}

		return deferred.promise;
	};

	var LoadFiles = function(files){
		var promises = [];
		for (var i = 0; i < files.length; i++) {
			var file = files[i];
			var id = $scope.attachments.length + i;
			promises.push(SetFiles(file, id));
		}
		$q.all(promises).then(function(response){
			_.forEach(response, function(attachment){
				$scope.attachments.push(attachment);
			});
			var attachment = $scope.attachments[$scope.attachments.length-1];
			$scope.SetActive(attachment);
			$scope.dataloading = false;
			$timeout(function() {
				document.querySelector('div.thumbnails').scrollLeft += (response.length * 120);
			});
		});
	};

	$scope.SetActive = function(attachment){
		if($scope.active != attachment.id)
			$scope.active = attachment.id;
	};

	$scope.LoadFiles = function(files){
		$scope.$apply(function () {
			$scope.dataloading = true;
			LoadFiles(files);
		});
	};

	$uibModalInstance.rendered.then(function(){
		LoadFiles($scope.files);
	});
}])


.controller('WarningCtrl', ['$scope', '$uibModalInstance', 'data',
	function ($scope, $uibModalInstance, data) {

	$scope.title = data.title;
	$scope.message = data.message;
	$scope.msg_close = data.msg_close;
	$scope.Close = function () {
		$uibModalInstance.close();
	};

}]);
