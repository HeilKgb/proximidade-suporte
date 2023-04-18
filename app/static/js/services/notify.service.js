'use strict';

angular.module('notifiy.factory', [])

.factory('Notify', ['notify', function(notify) {

	var history = [];

	var icons = {success: 'check_circle', error: 'error',
		info: 'info', warning: 'warning', warning2: 'warning'};
	var classes = {
		success: 'alert alert-success',
		error: 'alert alert-danger',
		info: 'alert alert-info',
		warning: 'alert alert-warning',
		warning2: 'alert alert-warning'
	};
	var messageTemplate = function(options) {
		return '<div class="notify-icon"><i class="material-icons">'+options.icon+'</i></div>'+
						'<div class="text-left"><h4 class="notify-title">'+ options.title + '</h4></div>'+
						'<div class="notify-text" ng-click="$close()">'+ options.message +'</div>';
	};
	var notify_dlg = function(data, type) {
		var message = data.message ? data.message : 'erro não identificado';
		var title = data.title ? data.title : 'Erro não identificado.';
		var opt = {icon: icons[type], title: title, message: message};
		data.container = data.container ? data.container : document.body;
		var mTemplate = messageTemplate(opt);
		var mtype = type;
		if(type == 'success')
			mtype = 'check_circle';
		history.push({
			date: new Date(),
			type: mtype,
			class: classes[type],
			title: title.replace(/<[^>]*>/g, ''),
			message: message.replace(/<[^>]*>/g, '')
		});
		return notify({ messageTemplate: mTemplate, classes: classes[type],
			position: data.position, container: data.container, duration: data.duration });
	};

	return {
		dlg: function(data, type) {
			notify_dlg(data, type);
		},
		success: function(data) {
			notify_dlg(data, 'success');
		},
		error: function(data) {
			notify_dlg(data, 'error');
		},
		info: function(data) {
			notify_dlg(data, 'info');
		},
		warning: function(data) {
			notify_dlg(data, 'warning');
		},
		warning2: function(data) {
			notify_dlg(data, 'warning2');
		},
		history: function(){
			return history;
		},
		notify: function(data_in){
			var data = {
				title: data_in.titulo,
				message: data_in.texto,
				position: data_in.position,
				duration: data_in.duration,
				container: data_in.container
			};
			switch (data_in.tipo){
				case 'success': notify_dlg(data, 'success'); break;
				case 'error': notify_dlg(data, 'error'); break;
				case 'warning': notify_dlg(data, 'warning'); break;
				default: notify_dlg(data, 'info'); break;
			}
		}
	};
}]);

/*  // Exemplo
	// Success
	Notify.success({
		title: "Succcess", message:'Succcess ao realizar o procedimento.',
		position: "right", // right, left, center
		duration: 3000     // milisecond
	});
	// Error
	Notify.error({
		title: 'Error', message: 'Erro ao realizar o procedimento',
		position: 'left', // right, left, center
		duration: 10000   // milisecond
	});
	// Info
	Notify.info({
		title: 'Info', message: 'Informação sobre o procedimento',
		position: 'left',  // right, left, center
		duration: 1000     // milisecond
	});
	// Warning
	Notify.warning({
		title: 'Warning',
		message: 'Warning ao realizar o procedimento !!',
		position: 'left',  // right, left, center
		duration: 1000     // milisecond
	});
*/
