/* jshint unused:vars */
'use strict';

angular.module('timeline.controller', [
	'carousel.media.controller'
])

.controller('TimelineCtrl', ['$scope', '$stateParams', '$q', 'current_user', '$uibModal',
  'DataService', 'sse',
	function($scope, $stateParams, $q, current_user, $uibModal, DataService, sse){

	$scope._ = _;
	$scope.loading = false;
	$scope.modalStatus = { isOpen: false };
	$scope.activity = null;
	$scope.comment = {'text': ''}
	$scope.config = $scope.lt.config;
	$scope.types_by_name = _.mapValues(_.keyBy($scope.config.types, 'name'), 'label');

	$scope.user = {
		name: current_user.fullname,
		email: current_user.email,
		organization: current_user.organization
	};

	var SetActivityScope = function(activity){
		$scope.activity = activity;
		if($scope.activity){
			$scope.timeline = $scope.activity.timeline;
			var type = $scope.activity.activity_type;
			$scope.phases = $scope.config.phases[type];
			$scope.nphases = $scope.phases.length;
			$scope.lastPhase = $scope.phases[$scope.nphases-1]['name'];
			$scope.status_phases = _.keyBy($scope.phases, 'name');

			var medias = [];
			_.forEach($scope.timeline, function(item, key){
				_.forEach(item.posts, function(post, jc){
					if(_.has(post, 'thumbnail') && (post.thumbnail.type == 'media')){
						var index = medias.length;
						medias.push({
							index: index,
							user: post.user,
							thumbnail: post.thumbnail,
							attachment: post.attachment,
							date: post.date
						});
					}
				});
			});
			$scope.medias = medias;
		}
	}

	$scope.btn_disabled = {avancar: false, pausar: false, executar: false, cancelar: false, finalizar: false};

	var watchActions = $scope.$watch(function() {
        return [$scope.activity];
    }, function() {
		$scope.updateStatus();
	}, true);
	$scope.$on('$destroy', function() {
        watchActions();
    });

	$scope.updateStatus = function(){
		$scope.btn_disabled.avancar = ($scope.activity.activity_phase == $scope.lastPhase || $scope.activity.activity_status.status != 'executando') ? true : false;
		$scope.btn_disabled.pausar = (
			$scope.activity.activity_status.status == 'cancelado' ||
			$scope.activity.activity_status.status == 'finalizado' ||
			$scope.activity.activity_phase == $scope.lastPhase) ? true : false;
		$scope.btn_disabled.executar = (
			$scope.activity.activity_status.status == 'cancelado' ||
			$scope.activity.activity_status.status == 'finalizado' ||
			$scope.activity.activity_phase == $scope.lastPhase) ? true : false;
		$scope.btn_disabled.cancelar = (
			$scope.activity.activity_status.status == 'cancelado' || $scope.activity.activity_status.status == 'finalizado') ? true : false;
		$scope.btn_disabled.finalizar = (
			$scope.activity.activity_status.status == 'cancelado' || $scope.activity.activity_status.status == 'finalizado') ? true : false;
	}

	var ConvertTextToUrl = function(text) {
		// convert text to url
		var exp = /(\b(https?|ftp|file):\/\/[-A-Z0-9+&@#\/%?=~_|!:,.;]*[-A-Z0-9+&@#\/%=~_|])/ig;
		var text1=text.replace(exp, "<a href='$1'>$1</a>");
		var exp2 =/(^|[^\/])(www\.[\S]+(\b|$))/gim;
		return (text1.replace(exp2, '$1<a target="_blank" href="http://$2">$2</a>'));
	};

	$scope.AddNewComment = function(){
		var post = {
			date: (new Date()).toISOString(),
			user: $scope.user,
			comment: ConvertTextToUrl($scope.comment.text)
		};
		var trello_post = {
			date: (new Date()).toISOString(),
			user: $scope.user,
			comment: ConvertTextToUrl($scope.comment.text)
		};
		// var index = _.findIndex($scope.timeline, {phase: $scope.activity.activity_phase});
		var index = $scope.timeline.length-1;
		if(index>-1){
			var timeline = angular.copy($scope.timeline);
			timeline[index].posts.push(post);
			$scope.comment.text = '';
			console.log(post);
			UpdateActivity({
				id: $scope.activity.id,
				data: {timeline: timeline},
				trello_data: {
					post: trello_post
				}
			});
		}
	};

	// Update Activity data
	var UpdateActivity = function(data_in){
		var trello_id = _.has($scope.activity, 'trello_cardId') ? $scope.activity['trello_cardId'] : null;
		var trello_data = data_in.trello_data;
		if (trello_id && trello_data)
			trello_data['id'] = trello_id
		DataService.UpdateActivity({
			data: data_in.data,
			trello_data: trello_data,
			method: 'PUT',
			url: '/activities/' + data_in.id,
		}).then(function(response){
			var activity = response.activity;
			var index = _.findIndex($scope.lt.activities, {id: activity.id});
			if(index>-1)
				$scope.lt.activities[index] = angular.copy(activity);
			SetActivityScope(activity);
			$scope.ShowNotify({
				texto: 'A atividade <span class="notify-texto">' + activity.title + '</span> foi atualizada.',
				titulo: 'Atualização da Atividade',
				tipo: 'info',
				position: 'right',
				duration: 4000,
				container: angular.element(document.querySelector("#id_notify"))
			});
		}, function(error){
			$scope.ShowNotify({
				texto: "Não foi possível atualizar a atividade.\n (" + error.data.message + ")",
				titulo: "Erro",
				tipo: 'error',
				position: 'right',
				duration: 5000,
				container: angular.element(document.querySelector("#id_notify"))
			});
		});
	};

	if($stateParams.id !== null){
		var activity = _.find($scope.lt.activities, function(item) {
			return item.id == $stateParams.id;
		});
		SetActivityScope(activity);
	}

	// Upload Attachments
	$scope.attachments = [];
	$scope.UploadFiles = function(appends){
		// var index = _.findIndex($scope.timeline, {phase: $scope.activity.activity_phase});
		var index = $scope.timeline.length-1;
		if(index>-1){
			var timeline = angular.copy($scope.timeline);
			var promises = _.map(appends, function(append){
				var file = append.file;
				var thumbnail = null;
				if (append.type == 'image' || append.type == 'video' || (append.type == 'application' && append.subtype == 'pdf')){
					thumbnail = append.thumbnail;
				}
				var deferred = $q.defer();
				console.log('file: %s thumbnail: %s', file, thumbnail)
				DataService.UploadFiles({file: file, thumbnail: thumbnail}).then(function(response){
					var post = {
						date: (new Date()).toISOString(),
						user: $scope.user,
						comment: append.comment,
						attachment: response.attachment,
						thumbnail: response.thumbnail
					};
					var attachment = {
						'name': response.attachment['filename'],
						'url': response.attachment['file']['url'],
						'comment': append.comment
					};
					deferred.resolve({post: post, attachment: attachment});
				});
				return deferred.promise;
			});
			$q.all(promises).then(function(response){
				var attachments = [];
				_.forEach(response, function(resp){
					attachments.push(resp.attachment);
					timeline[index].posts.push(resp.post);
				});

				UpdateActivity({
					id: $scope.activity.id,
					data: {timeline: timeline},
					trello_data: {
						attachments: attachments
					}
				});
			});
		}
	};

	$scope.ChangeStatus = function(status){

		var activity_status = {
			status: status,
			date : (new Date()).toISOString(),
			user: $scope.user
		}
		var comment = _.result(_.find($scope.config.status, {name: status}),'comment')

		UpdateActivity({
			id: $scope.activity.id,
			data: {activity_status: activity_status},
			trello_data: {
				status: {
					comment: comment,
					user: $scope.user,
					status: status
				}
			}
		});
	};

	$scope.AdvanceStage = function(activity_phase){
		var index = _.findIndex($scope.phases, {'name': activity_phase})
		index++;
		if(index < $scope.nphases){
			var modalScope = $scope.$new();
			modalScope.title = 'Avançar Fase';
			modalScope.message = 'Deseja avançar para a fase <span class="badge ' +$scope.phases[index]['label'] + '">' + $scope.phases[index]['label']  + '</span>?';
			modalScope.comment = {text: ''};
			var modalInstance = $uibModal.open({
				templateUrl: 'change.phase.tpl.html',
				scope: modalScope,
				backdrop: 'static',
			});
			modalInstance.result.then(function (result) {
				$scope.activity.activity_phase = $scope.phases[index]['name'];
				$scope.activity.activity_phase_label = $scope.phases[index]['label'];
				var nf = {
					index: $scope.activity.timeline.length,
					phase: $scope.phases[index]['name'],
					user: $scope.user,
					date: (new Date()).toISOString(),
					posts: []
				};
				var timeline = angular.copy($scope.timeline);
				timeline.push(nf);
				var comment = $scope.status_phases[$scope.activity.activity_phase]['comment'];
				UpdateActivity({
					id: $scope.activity.id,
					data: {activity_phase: $scope.activity.activity_phase, timeline: timeline},
					trello_data: {
						phase: {
							phase: $scope.phases[index]['name'],
							comment: comment,
							user: $scope.user,
							date: (new Date()).toISOString()
						}
					}
				});
			}, function () {
				console.log('Modal dismissed at: ' + new Date());
			});
			modalScope.ok = function (){
				modalInstance.close();
			};
			modalScope.cancel = function(){
				modalInstance.dismiss();
			};
		}
	};

	$scope.views = {option: 'main'};

	// Open a Modal Carousel
	$scope.childObj = {};
	$scope.ShowCarousel = function(attachment){
		$scope.views.option = 'carousel';
		var media = _.find($scope.medias, {attachment: attachment});
		$scope.childObj.SetActive(media);
	};

	$scope.Approve = function(){
		var index = _.findIndex($scope.phases, {'name': $scope.activity.activity_phase})
		if (index != -1){
			index++;
			$scope.activity.activity_phase = $scope.phases[index]['name'];
			$scope.activity.activity_phase_label = $scope.phases[index]['label'];
			var nf = {
				index: $scope.activity.timeline.length,
				phase: $scope.phases[index]['name'],
				user: $scope.user,
				date: (new Date()).toISOString(),
				posts: [{
					date: (new Date()).toISOString(),
					user: $scope.user,
					comment: ConvertTextToUrl('Estou de acordo com a solução apresentada, e a solicitação foi atendida.')
				}]
			};
			var timeline = angular.copy($scope.timeline);
			timeline.push(nf);
			var comment = $scope.status_phases[$scope.activity.activity_phase]['comment'];

			UpdateActivity({
				id: $scope.activity.id,
				data: {activity_phase: $scope.activity.activity_phase, timeline: timeline},
				trello_data: {
					approve: true,
					phase: {
						phase: $scope.phases[index]['name'],
						comment: comment + '. Cliente deu ciência e aprovou a solução.',
						user: $scope.user,
						date: (new Date()).toISOString()
					}
				}
			});
		}
	};

	sse.addEventListener('message', function (e) {
		var data = e;
		if (e.data){
			try {
				data = JSON.parse(e.data);
				if ($scope.activity.id == data['id']){
					var atype = $scope.activity.activity_type;
					if (data['tipo'] == 'updateFields'){
						if ('closed' in data['data']){
							var message = data['data']['close'] == true ? 'Uma solicitação foi desativado.' : 'Uma solicitação foi reativada.';
							CanReload({
								title: title,
								message: message + "<br> Deseja recarregar as solicitações?"
							}).then(function(resp){
								$window.location.reload();
							}, function(error){
							});
						}
						else{
							_.forOwn(data['data'], function(value, key){
								$scope.activity[key] = value;
							});
						}
					}
					if (data['tipo'] == 'updatePhase'){
						var aphase = _.find($scope.config.phases[atype], {name: data['data']['phase']})

						$scope.activity.activity_phase = data['data']['phase'];
						$scope.activity.activity_phase_label = aphase['label'];
						$scope.activity.timeline.push(data['data']);
					}
					if (data['tipo'] == 'addComment'){
						if ('timeline_id' in data){
							$scope.activity.CanApprove = false;
							var phases = $scope.config.phases[atype];
							$scope.activity.CanApprove = false;
							$scope.activity.timeline[data['timeline_id']]['posts'].push(data['data']);
							_.forEach($scope.activity.timeline, function(item, key){
								_.forEach(item.posts, function(post, jc){
									if ($scope.activity.activity_phase != phases[phases.length-2]['name'] &&
										_.includes(post.comment, 'clique no botão "Aprovar"'))
										$scope.activity.CanApprove = true;
								});
							});
						}
					}
					if (data['tipo'] == 'updateComment'){
						$scope.activity.timeline[data['timeline_id']]['posts'][data['pid']] = data['data'];
						var phases = $scope.config.phases[atype];
						if ($scope.activity.activity_phase != phases[phases.length-2]['name'] &&
							_.includes(data['data'].comment, 'clique no botão "Aprovar"'))
							$scope.activity.CanApprove = true;
						else
							$scope.activity.CanApprove = false;
					}
					if (data['tipo'] == 'deleteComment'){
						$scope.activity.timeline[data['timeline_id']]['posts'] = data['data'];
						var phases = $scope.config.phases[atype];
						if ($scope.activity.activity_phase != phases[phases.length-2]['name'] &&
							_.includes(data['data'].comment, 'clique no botão "Aprovar"'))
							$scope.activity.CanApprove = true;
						else
							$scope.activity.CanApprove = false;
					}
					if (data['tipo'] == 'run_action_to_finish'){
						$scope.activity.activity_status = data['data'];
						$scope.updateStatus();
					}
				}
			} catch (err) {
				console.log(err);
				console.log(e);
			}
		}
	});

	var CanReload = function(data){
		var deferred = $q.defer();
		var Scope = $scope.$new();
		Scope.title = data.title;
		Scope.message = data.message;
		$uibModal.open({
			templateUrl: 'confirmacao.tpl.html',
			scope: Scope,
			backdrop: false,
			controller: ['$scope', '$uibModalInstance',
				function($scope, $uibModalInstance){
					$scope.Cancel= function(){
						$uibModalInstance.dismiss();
					};
					$scope.Ok = function(){
						$uibModalInstance.close();
					};
				}
			]
		}).result.then(function () {
			deferred.resolve();
		}, function (error){
			deferred.reject(error);
		});
		return deferred.promise;
	};
}]);
