/* jshint unused:vars */
'use strict';

angular.module('activities.controller', [])

.controller('ActivitiesCtrl', ['$scope', '$state', '$q', '$window', '$uibModal', 'DataService',
  'apps_data', 'lt_data', 'sse',
  function($scope, $state, $q, $window, $uibModal, DataService, apps_data, lt_data, sse){

	$scope._ = _;

	$scope.$parent.mainloading = false;
	$scope.reverse = true;
	$scope.predicate = 'created_at';
	$scope.order = function(predicate) {
   		$scope.reverse = ($scope.predicate === predicate) ? !$scope.reverse : false;
    	$scope.predicate = predicate;
	};

	$scope.$parent.lt.activities = lt_data.activities;
	$scope.$parent.lt.config = lt_data.config;
	$scope.lt.config.module = _.find(apps_data.apps, app => _.includes($scope.appUrl, app.url));
	$scope.lt.config.modules = apps_data.apps;
	$scope.types_by_name = _.mapValues(_.keyBy($scope.lt.config.types, 'name'), 'label');

	var UpdateAfterDelete = function(response){
		_.remove($scope.lt.activities, {'id': response.data.id});
		$scope.ShowNotify({
			texto: 'A solicitação <span class="notify-texto">"' + response.data.title + '"</span> foi removida com sucesso.',
			titulo: "Solicitação Removida",
			tipo: 'info',
			position: 'right',
			duration: 3000,
			container: angular.element(document.querySelector("#id_notify"))
		});
	};

	$scope.DeleteActivity =  function(item){
		DataService.DeleteActivity({id: item.id}).then(function(response){
			var modalScope = $scope.$new();
			modalScope.title = 'Remover';
			modalScope.message = 'Deseja remover esta solicitação ?';
			var modalInstance = $uibModal.open({
				templateUrl: 'delete.activity.tpl.html',
				scope: modalScope
			});
			var token = response.token;
			modalInstance.result.then(function (result) {
				DataService.DeleteActivity({id: item.id, token: token.id})
				.then(function(response){
					UpdateAfterDelete(response);
				}, function(error){
					$scope.ShowNotify({
						texto: "Não foi possível excluir esta solicitação.\n (" + error.data.message + ")",
						titulo: "Erro",
						tipo: 'error',
						position: 'right',
						duration: 3000,
						container: angular.element(document.querySelector("#id_notify"))
					});
				});
			}, function () {
			});
			modalScope.ok = function (){
				modalInstance.close();
			};
			modalScope.cancel = function(){
				modalInstance.dismiss();
			};
		}, function(error){
			$scope.ShowNotify({
				texto: "Não foi possível apagar esta solicitação.\n (" + error.data.message + ")",
				titulo: "Erro",
				tipo: 'error',
				position: 'right',
				duration: 5000,
				container: angular.element(document.querySelector("#id_notify"))
			});
		});
	};

	$scope.ShowMobile = function(item, value){
		DataService.UpdateActivity({
			data: {mobile: value},
			method: 'PUT',
			url: '/activities/' + item.id
		}).then(function(response){
			var activity = response.activity;
			var idx = _.findIndex($scope.lt.activities, {'id': activity.id});
			$scope.lt.activities[idx] = activity;
			if(value){
				$scope.ShowNotify({
					texto: 'A notificação da solicitação <span class="notify-texto">"' + activity.title + '"</span> no aplicativo foi ativada.',
					titulo: 'Notificação',
					tipo: 'info',
					position: 'right',
					duration: 4000,
					container: angular.element(document.querySelector("#id_notify"))
				});
			}
			else{
				$scope.ShowNotify({
					texto: 'A notificação da solicitação <span class="notify-texto">"' + activity.title + '"</span> no aplicativo foi desativada.',
					titulo: 'Notificação',
					tipo: 'info',
					position: 'right',
					duration: 4000,
					container: angular.element(document.querySelector("#id_notify"))
				});
			}

		}, function(error){
			$scope.ShowNotify({
				texto: "Não foi possível alterar a opção de notificação no smartphone.\n (" + error.data.message + ")",
				titulo: "Erro",
				tipo: 'error',
				position: 'right',
				duration: 5000,
				container: angular.element(document.querySelector("#id_notify"))
			});
			console.log(error);
		});
	};

	$scope.ArchiveActivity = function(item, value){
		DataService.UpdateActivity({
			data: {closed: value},
			method: 'PUT',
			url: '/activities/' + item.id
		}).then(function(response){
			var activity = response.activity;
			var idx = _.findIndex($scope.lt.activities, {'id': activity.id});
			$scope.lt.activities[idx] = activity;
			if(value){
				$scope.ShowNotify({
					texto: 'A  solicitação <span class="notify-texto">"' + activity.title + '"</span> no aplicativo foi arquivada.',
					titulo: 'Notificação',
					tipo: 'info',
					position: 'right',
					duration: 4000,
					container: angular.element(document.querySelector("#id_notify"))
				});
				$window.location.reload();
			}
			else{
				$scope.ShowNotify({
					texto: 'A solicitação <span class="notify-texto">"' + activity.title + '"</span> no aplicativo foi restaurada.',
					titulo: 'Notificação',
					tipo: 'info',
					position: 'right',
					duration: 4000,
					container: angular.element(document.querySelector("#id_notify"))
				});
				$window.location.reload();
			}

		}, function(error){
			$scope.ShowNotify({
				texto: "Não foi possível alterar..\n (" + error.data.message + ")",
				titulo: "Erro",
				tipo: 'error',
				position: 'right',
				duration: 5000,
				container: angular.element(document.querySelector("#id_notify"))
			});
			console.log(error);
		});
	}

	$scope.UpdateAfterAdd = function (data){
		$scope.lt.activities.push(data);
	};

	$scope.UpdateActivity = function(data){
		var index = _.findIndex($scope.lt.activities, {id: data.id});
		if(index>-1)
			$scope.lt.activities[index] = angular.copy(data);
	};

	sse.addEventListener('message', function (e) {
		var data = e;
		if (e.data){
			try {
				data = JSON.parse(e.data);

				var atividade = _.find($scope.lt.activities, {id: data['id']});
				var atype = atividade.activity_type;
				var timeline = atividade.timeline;
				if (data['tipo'] == 'updateFields'){
					if ('closed' in data['data']){
						var message = data['data']['close'] == true ? 'Uma solicitação foi desativado.' : 'Uma solicitação foi reativada.';
						$scope.ShowNotify({
							titulo: 'Atualização',
							texto: message,
							tipo: 'info',
							position: 'right',
							duration: 6000,
							container: angular.element(document.querySelector("#id_notify"))
						});
						CanReload({
							title: title,
							message: message + "<br> Deseja recarregar as solicitações?"
						}).then(function(resp){
							$window.location.reload();
						}, function(error){
						});
					}
					else{
						var campo = {
							title: 'Título',
							description: 'Descrição',
						};
						var title = 'Atualização';
						var message = 'Existe uma atualização na solicitação.';
						var message2 = 'Deseja recarregá-la?';
						var message3 = 'Solicitação atualizada com sucesso';
						if (Object.keys(data['data']).length){
							title = 'Atualizações';
							message = "Existem atualizações na solicitação.";
							message2 = 'Deseja recarregá-las?';
							message3 = 'Solicitações atualizadas com sucesso.';
						}
						_.forOwn(data['data'], function(value, key){
							$scope.ShowNotify({
								titulo: 'Atualização',
								texto: 'O campo ' + campo[key] + ' foi atualizado para "' + value + '"',
								tipo: 'info',
								position: 'right',
								duration: 5000,
								container: angular.element(document.querySelector("#id_notify"))
							});
						});
						CanReload({
							title: title,
							message: message + "<br>" + message2
						}).then(function(resp){
							_.forOwn(data['data'], function(value, key){
								atividade[key] = value;
								$scope.ShowNotify({
									titulo: title,
									texto: message3,
									tipo: 'info',
									position: 'right',
									duration: 3000,
									container: angular.element(document.querySelector("#id_notify"))
								});
							});
						}, function(error){
						});
					}
				}
				if (data['tipo'] == 'updatePhase'){
					var aphase = _.find($scope.lt.config.phases[atype], {name: data['data']['phase']})
					$scope.ShowNotify({
						titulo: 'Atualizada:',
						texto: 'A solicitação foi atualizada para ' + aphase['label'],
						tipo: 'info',
						position: 'right',
						duration: 6000,
						container: angular.element(document.querySelector("#id_notify"))
					});
					CanReload({
						title: "Carregar solicitação",
						message: "Deseja carregar a solicitação atualizada?"
					}).then(function(resp){
						atividade.activity_phase = data['data']['phase'];
						atividade.activity_phase_label = aphase['label'];
						atividade.timeline.push(data['data']);
						if (data['activity_status']){
							atividade.activity_status = data['activity_status']
							atividade.activity_status.date = new Date(atividade.activity_status.date);
						}
						$state.go('solicitacao', {'id': atividade.id});
					}, function(error){

					});
				}
				if (data['tipo'] == 'addComment'){
					var comment = data['data']['comment'];
					$scope.ShowNotify({
						titulo: 'Nova mensagem:',
						texto: comment,
						tipo: 'info',
						position: 'right',
						duration: 6000,
						container: angular.element(document.querySelector("#id_notify"))
					});

					CanReload({
						title: "Carregar solicitação",
						message: "Deseja carregar a solicitação atualizada?"
					}).then(function(resp){
						atividade.CanApprove = false;
						var phases = $scope.lt.config.phases[atype];
						atividade.timeline[data['timeline_id']]['posts'].push(data['data']);
						_.forEach(atividade.timeline, function(item, key){
							_.forEach(item.posts, function(post, jc){
								if (atividade.activity_phase != phases[phases.length-2]['name'] &&
									_.includes(post.comment, 'clique no botão "Aprovar"'))
									atividade.CanApprove = true;
							});
						});
						$state.go('solicitacao', {'id': atividade.id});
					}, function(error){

					});
				}
				if (data['tipo'] == 'updateComment'){
					var comment = data['data']['comment'];
					$scope.ShowNotify({
						titulo: 'Atualização da solicitação',
						texto: comment,
						tipo: 'info',
						position: 'right',
						duration: 6000,
						container: angular.element(document.querySelector("#id_notify"))
					});
					CanReload({
						title: "Carregar solicitação",
						message: "Deseja carregar a solicitação atualizada?"
					}).then(function(resp){
						atividade.timeline[data['timeline_id']]['posts'][data['pid']] = data['data'];
						$state.go('solicitacao', {'id': atividade.id});
					}, function(error){

					});
				}
				if (data['tipo'] == 'deleteComment'){
					var comment = data['data']['comment'];
					$scope.ShowNotify({
						titulo: 'Atualização da solicitação:',
						texto: comment,
						tipo: 'info',
						position: 'right',
						duration: 6000,
						container: angular.element(document.querySelector("#id_notify"))
					});
					CanReload({
						title: "Atualização da solicitação",
						message: "Deseja carregar a solicitação atualizada?"
					}).then(function(resp){
						atividade.timeline[data['timeline_id']]['posts'] = data['data'];
						$state.go('solicitacao', {'id': atividade.id});
					}, function(error){

					});
				}
				if (data['tipo'] == 'run_action_to_finish'){
					$scope.ShowNotify({
						titulo: 'Atualização da solicitação:',
						texto: comment,
						tipo: 'info',
						position: 'right',
						duration: 6000,
						container: angular.element(document.querySelector("#id_notify"))
					});

					CanReload({
						title: "Carregar solicitação",
						message: "Deseja carregar a solicitação atualizada?"
					}).then(function(resp){
						atividade.activity_status = data['data'];
						$state.go('solicitacao', {'id': atividade.id});
					}, function(error){

					});
				}
			} catch (error) {
				console.log(error);
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
