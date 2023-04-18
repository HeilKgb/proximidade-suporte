/* jshint unused:vars */
/*jshint unused:false*/
'use strict';

angular.module('data.service', [])

.factory('DataService',['$http', '$q', '$cookies', 'Notify', function($http, $q, $cookies, Notify){

	// return a thumbnail type
	var Thumbnail = function (attachment){
		try{
			var tipo = attachment.image_type.split("/")[0];
			var app =  attachment.image_type.split("/")[1];
			var extension = attachment.filename.replace(/^.*?\.([a-zA-Z0-9]+)$/, "$1").toLowerCase();
			if (!attachment.file.url)
				return {src: '', type: ''};
			switch (tipo){
				case 'image': return {src: attachment.thumbnail.url, type: 'media', subtype: 'image'}; break;
				case 'video': return {src: attachment.thumbnail.url, type: 'media', subtype: 'video'}; break;
				case 'audio': return {src: "/static/icons/audio-player.ico", type: 'media', subtype: 'audio'}; break;
				case 'application':
					switch (app){
						case 'pdf': return {src: attachment.thumbnail.url, type: 'pdf'}; break;

						case 'msword':
						case 'vnd.openxmlformats-officedocument.wordprocessingml.document':
							return {src: '/static/images/msword.png', type: 'msoffice'}; break;

						case 'vnd.ms-excel':
						case 'vnd.openxmlformats-officedocument.spreadsheetml.sheet':
							return {src: '/static/images/msexcel.png', type: 'msoffice'}; break;

						case 'vnd.ms-powerpoint':
						case 'vnd.openxmlformats-officedocument.presentationml.presentation':
							return {src: '/static/images/mspowerpoint.png', type: 'msoffice'}; break;

						case 'json':
							return {src: '/static/images/json.png', type: 'json'}; break;

						default: return {src: '', type: '', extension: extension}; break;
					}
				break;
				case 'text': return {src: '', type: 'text', extension: extension}; break;
				case 'csv': return {src: '', type: 'csv', extension: extension}; break;
				case 'json': return {src: '/static/images/json.png', type: 'json', extension: extension}; break;
				default: return {src: '', type: ''}; break;
			};
		}
		catch{
			return {src: '', type: ''};
		}
	};

	// Adjust Activities after loaded from database
	var AdjustToLoad = function(datas, config){
		if ( datas !== undefined && datas instanceof Array){
			// return _.map(_.filter(datas, data => !data.closed), function(value, key) {
			return _.map(datas, function(value, key) {
		 		// Transformar ISOString to Date
				value.CanApprove = false;
				value.created_at = value.created_at ? new Date(value.created_at) : null;
				value.updated_at = value.updated_at ? new Date(value.updated_at) : null;
				value.activity_status.date = value.activity_status.date ? new Date(value.activity_status.date) : null;

				var timeline = value.timeline[value.timeline.length-1]
				value.activity_phase = timeline ? timeline['phase'] : 'recebido';
				var type = value.activity_type;
				var phases = config['phases'][type];
				value.activity_phase_label = _.find(phases, ['name', value.activity_phase])['label']
				_.forEach(value.timeline, function(item, key){
					item.date = item.date ? new Date(item.date): null;
					_.forEach(item.posts, function(post, jc){
						post.date = post.date ? new Date(post.date): null;
						if(_.has(post, 'attachment') && post.attachment != null){
							post.thumbnail = Thumbnail(post.attachment);
						}
						if (value.activity_phase != phases[phases.length-2]['name'] &&
							(jc == item.posts.length-1) &&
							_.includes(post.comment, 'clique no botão "Aprovar"'))
							value.CanApprove = true;
					});
				});
				return value;
			});
		}
		else{
			datas.created_at = datas.created_at ? new Date(datas.created_at): null;
			datas.updated_at = datas.updated_at ? new Date(datas.updated_at): null;
			datas.CanApprove = false;

			var timeline = datas.timeline[datas.timeline.length-1]
			datas.activity_phase = timeline ? timeline['phase'] : 'recebido';
			var type = datas.activity_type;
			var phases = config['phases'][type];
			datas.activity_phase_label = _.find(phases, ['name', datas.activity_phase])['label']
			_.forEach(datas.timeline, function(item, key){
				item.date = item.date ? new Date(item.date) : null;
				_.forEach(item.posts, function(post, jc){
					post.date = post.date ? new Date(post.date): null;
					if(_.has(post, 'attachment') && post.attachment != null){
						post.thumbnail = Thumbnail(post.attachment);
					}
					if (datas.activity_phase != phases[phases.length-2]['name'] &&
						_.includes(post.comment, 'clique no botão "Aprovar"'))
						datas.CanApprove = true;
				});
			});

			return datas;
		}
	};

	// Adjust Activities to Save in Database
	var AdjustToSave = function(data_in){
		var data = angular.copy(data_in.data);

		if (data.timeline){
			_.forEach(data.timeline, function(timeline, i){
				timeline.user = timeline.user.email;
				_.forEach(timeline.posts, function(post, j){
					if (_.isObject(post.user))
						post.user = post.user.email;
					delete post.thumbnail;
				});
			});
		}
		if ('activity_status' in data && _.isObject(data.activity_status.user)){
			data.activity_status.user = data.activity_status.user.email;
		}
		var trello_data = _.has(data_in, 'trello_data') ? data_in['trello_data'] : {};

		delete data.$$hashKey;
		return {data: data, trello_data: trello_data};
	};

	// Handler to load applications
	var GetApplications = function(data_in){
		var deferred = $q.defer();
		$http.get(data_in.url).then(function(response){
			var data_out = response.data.data;
			deferred.resolve(data_out);
		}, function(error){
			if (error.status == 404)
				deferred.resolve([]);
			else{
				var message = 'Não foi possível retornar os aplicativos.';
				if (error && error['data'] && error['data']['message'])
					message = error['data']['message'];

				Notify.error({
					title: 'FALHA!',
					message: message,
					position: "right",
					duration: 4000,
					container: angular.element(document.querySelector("#id_notify"))
				});
				deferred.reject(error);
			}
		});
		return deferred.promise;
	};

	// Handler to load Activities
	var GetLTData = function(data_in){
		var deferred = $q.defer();
		$http.get(data_in.url).then(function(response){
			var data_out = response.data.data;
			if (!_.isEmpty(data_out.activities)){
				if ( data_out.activities !== undefined && !(data_out.activities instanceof Array)){
					data_out.activities = JSON.parse(data_out.activities);
				}
				data_out.activities = AdjustToLoad(data_out.activities, data_out.config);
			}
			deferred.resolve(data_out);
		}, function(error){
			if (error.status == 404)
				deferred.resolve([]);
			else{
				var message = 'Não foi possível retornar os aplicativos.';
				if (error && error['data'] && error['data']['message'])
					message = error['data']['message'];

				Notify.error({
					title: 'FALHA!',
					message: message,
					position: "right",
					duration: 4000,
					container: angular.element(document.querySelector("#id_notify"))
				});
				deferred.reject(error);
			}
		});
		return deferred.promise;
	};

	// Handler to load organizations
	var GetOrganizations = function(data_in){
		var deferred = $q.defer();
		$http.get(data_in.url).then(function(response){
			var data_out = response.data.data;
			deferred.resolve(data_out.organizations);
		}, function(error){
			if (error.status == 404)
				deferred.resolve([]);
			else{
				var message = 'Não foi possível retornar as organizações.';
				if (error && error['data'] && error['data']['message'])
					message = error['data']['message'];

				Notify.error({
					title: 'FALHA!',
					message: message,
					position: "right",
					duration: 4000,
					container: angular.element(document.querySelector("#id_notify"))
				});
				deferred.reject(error);
			}
		});
		return deferred.promise;
	};

	// Handler to create new Activity
	var CreateNewActivity = function (data_in) {
		var deferred = $q.defer();
		var xsrfcookie = $cookies.get('_xsrf');
		var data = AdjustToSave(data_in);
		$http({
			method: data_in.method,
			url: data_in.url,
			data: data,
			headers: { 'Content-Type':'application/json', 'X-XSRFToken':xsrfcookie },
			config: {}
		}).then(function(response){
			var data = response.data.data;
			deferred.resolve({activity: AdjustToLoad(data.activities, data.config)});
		}, function(error){
			deferred.reject(error);
		});
		return deferred.promise;
	};

	var DeleteActivity = function (data) {
		var deferred = $q.defer();
		var xsrfcookie = $cookies.get('_xsrf');
		var url = '/activities/' + data.id;
		if (data.token)
			url += '?token=' + data.token;
		$http({
			method: 'DELETE',
			url: url,
			headers: { 'Content-Type': 'application/json', 'X-XSRFToken' : xsrfcookie },
			config: {}
		}).then(function(response){
			deferred.resolve(response.data);
		}, function(error){
			if(error.status == 401)
				deferred.resolve({token: error.data.data.token});
			else
				deferred.reject(error);
		});
		return deferred.promise;
	};

	// Handler to Update Activity id, data_in
	var UpdateActivity = function (data_in) {
		var deferred = $q.defer();
		var xsrfcookie = $cookies.get('_xsrf');
		var data = AdjustToSave(data_in);
		$http({
			method: data_in.method,
			url: data_in.url,
			data: data,
			headers: { 'Content-Type': 'application/json', 'X-XSRFToken' : xsrfcookie},
			config: {}
		}).then(function(response){
			var resp = response.data.data;
			deferred.resolve({activity: AdjustToLoad(resp.activities, resp.config)});
		}, function(error){
			deferred.reject(error);
		});data
		return deferred.promise;
	};

	// Handler to upload files
	var UploadFile = function(formData, type){
		var xsrfcookie = $cookies.get('_xsrf');
		var deferred = $q.defer();
		$http({
			method: 'POST', url: '/files/upload', data: formData,
			headers: {
				'Content-Type': undefined,
				'X-XSRFToken' : xsrfcookie,
				'File-Service':'suporte'
			},
			config: {}
		})
		.then(function(response){
			deferred.resolve({type: type, success: true, data: response});
		}, function(response){
			if (response.status == 409)
				deferred.resolve({type: type, success: true, data: response});
			else
				deferred.resolve({type: type, success: false, data: response});
		});
		return deferred.promise;
	};

	// Upload Files
	var UploadFiles = function (input_data) {
		var requests = [];
		var formData = new FormData();
		// Main File
		formData.append('file', input_data.file);
		requests.push(UploadFile(formData, 'filename'));
		// Thumbnail
		if(input_data.thumbnail){
			var fData = new FormData();
			fData.append('file', input_data.thumbnail.blob, input_data.thumbnail.filename);
			requests.push(UploadFile(fData, 'thumbnail'));
		}

		var deferred = $q.defer();
		$q.all(requests).then(function (response){
			var attachment = {};
			_.forEach(response, function(resp){
				if (resp.success){
					var data = resp.data.data.data;
					if (resp.type == 'filename'){
						attachment['filename'] = input_data.file.name;
						attachment['image_type'] = input_data.file.type;
						attachment['file'] = {
							url : data.url,
							checksum: data.checksum
						};
					}
					if (resp.type == 'thumbnail'){
						attachment['thumbnail'] = {
							url: data.url,
							checksum: data.checksum
						};
					}
				}
				else{
					Notify.error({
						title: 'Erro',
						message: resp.data.data.message,
						position: 'right',
						duration: 3000,
						container: angular.element(document.querySelector("#id_notify"))
					});
				}
			});
			var outdata = {
				attachment: attachment,
				thumbnail: Thumbnail(attachment)
			};
			deferred.resolve(outdata);
		});
		return deferred.promise;
	};

	var Service = {
		GetApplications: GetApplications,
		GetLTData: GetLTData,
		GetOrganizations: GetOrganizations,
		CreateNewActivity: CreateNewActivity,
		DeleteActivity: DeleteActivity,
		UpdateActivity: UpdateActivity,
		UploadFiles: UploadFiles
	};

	return Service;
}]);


