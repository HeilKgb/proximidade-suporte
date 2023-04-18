/* jshint unused:vars */
'use strict';

angular.module('add-activity.controller', [
	'attach-files.controller'
])

	.controller('AddActivityCtrl', ['$scope', '$q', '$uibModalInstance', 'user', 'config',
		'DataService', 'Notify',
		function ($scope, $q, $uibModalInstance, user, config, DataService, Notify) {

			$scope._ = _;

			$scope.user = user;
			$scope.config = config;
			$scope.modalStatus = { isOpen: false };

			// Activity
			$scope.activity = {
				user: {
					email: $scope.user.email,
					name: $scope.user.fullname,
					organization: $scope.user.organization
				},
				organizations: _.uniq(_.concat(['Proximidade_suporte'], [$scope.user.organization])),
				description: '',
				activity_type: $scope.config.types[0].name
			}

			$scope.title = 'Solicitação de Suporte';

			$scope.Cancel = function () {
				console.log("Close");
				$uibModalInstance.dismiss("close");
			};

			$scope.attachments = [];
			$scope.dataLoading = false;

			// Attachments List
			$scope.AttachedFiles = function (attachments) {
				$scope.attachments = attachments;
				console.log(attachments);
			};

			// Removing attachments
			$scope.RemoveAttachment = function (attachment) {
				_.remove($scope.attachments, attachment);
				Reindex();
				if ($scope.attachments.length > 0)
					$scope.SetActive($scope.attachments[0]);
			};

			$scope.SetActive = function (attachment) {
				if ($scope.active != attachment.id)
					$scope.active = attachment.id;
			};

			function Reindex() {
				_.forEach($scope.attachments, function (attachment, index) {
					attachment.id = index;
				});
			};

			function addHours(date, hours) {
				return new Date(date.getTime() + hours * 60 * 60 * 1000);
			}

			function dueDate(due_date) {
				// 0 - Sunday, 1- Monday, 2- Tuesday, 3- Wednesday
				// 4 - Thursday, 5- Friday, 6- Saturday
				if (due_date.getDay() == 5) {
					return addHours(new Date(), 4 * 24);
				}
				else if (due_date.getDay() == 6) {
					return addHours(new Date(), 3 * 24);
				}
				else if (due_date.getDay() == 0) {
					return addHours(new Date(), 2 * 24);
				}
				else {
					return addHours(new Date(), 24);
				}
			}
			// Create a activity
			$scope.Submit = function (form) {
				if ($scope.dataloading)
					return;
				if (form.$valid) {
					$scope.dataloading = true;
					UploadAttachments().then(function (response) {
						CreateNewActivity(response);
					});
				}
			};

			var CreateNewActivity = function (data_in) {
				var date = (new Date()).toISOString();
				var activity_status = {
					status: $scope.config.status[0]['name'],
					user: $scope.activity.user['email'],
					date: date
				};
				var posts = [{
					date: date,
					user: $scope.activity.user,
					comment: $scope.activity.description
				}];
				var activity_type = $scope.config.types[0];
				var activity_phase = $scope.config.phases[activity_type['name']][0];
				var title = 'Solicitação do Suporte';
				var data = {
					title: title,
					created_by: $scope.activity.user['email'],
					organizations: $scope.activity.organizations,
					description: $scope.activity.description,
					trello_cardId: null,
					mobile: false,
					activity_type: activity_type['name'],
					module: $scope.config.module,
					activity_status: activity_status,
					timeline: [{
						index: 0,
						phase: activity_phase['name'],
						user: $scope.activity.user,
						date: date,
						posts: _.concat(posts, data_in.posts)
					}],
					closed: false
				};
				var due_date = dueDate(new Date());
				var client_message = $scope.activity.user['name'] +
					'(' + $scope.activity.user['email'] + ')' + ' da empresa: ' +
					$scope.activity.user['organization'] +
					' solicitou suporte para o seguinte problema: ' + data.description;
				var trello_data = {
					name: data.title,
					desc: data.description,
					due_date: due_date.toISOString(),
					organizations: data.organizations,
					activity_type: activity_type['label'],
					idMembers: $scope.config.module.manager ? [$scope.config.module.manager.id] : [],
					cardPosition: 'bottom', // posição do cartão na lista
					checklist: {
						name: 'Atividades',
						checkitems: [
							{ name: 'Definir um prazo com o cliente (enviar mensagem citando #cliente)', checked: 'false' },
							{ name: 'O prazo de entrega (Due date) foi ajustado com a data combinada com o cliente', checked: 'false' }
							// {'name': 'Alocar um analista para a tarefa', 'checked': 'false'},
							// {'name': 'Definir um prazo para a tarefa', 'checked': 'false'}
						]
					},
					attachments: data_in.trello,
					client: $scope.activity.user,
					posts: [client_message, '@' +
						$scope.config.module.manager.username +
						', este cartão foi alocado para você.\n' +
						'Você tem 24h para responder.']
				};
				// Create activity / trello card
				DataService.CreateNewActivity({
					data: data,
					trello_data: trello_data,
					method: 'POST',
					url: '/activities'
				}).then(function (response) {
					console.log(response);
					$scope.activity = response.activity;
					$scope.dataloading = false;
					if ($scope.activity.trello_cardId) {
						Notify.success({
							title: 'Informação',
							message: 'Uma nova solicitação foi cadastrada.',
							position: 'right',
							duration: 3000,
							container: angular.element(document.querySelector('#id_notify'))
						});
					}
					else {
						Notify.error({
							title: 'Erro',
							message: 'Infelizmente houve um erro interno e não conseguimos seguir por aqui. \n' +
								'Favor enviar um email para suporte.prox@venidera.com',
							position: 'right',
							duration: 8000,
							container: angular.element(document.querySelector('#id_notify'))
						});
					}
					$uibModalInstance.close($scope.activity);
				}, function (error) {
					$scope.dataloading = false;
					console.log(error);
					Notify.error({
						title: 'Erro',
						message: 'Não foi possível cadastrar esta solicitação.\n (' + error.data.message + ')',
						position: 'right',
						duration: 3000,
						container: angular.element(document.querySelector('#id_notify'))
					});
				});
			};

			// Upload Attachments
			var UploadAttachments = function () {
				var defer = $q.defer();
				if (_.isEmpty($scope.attachments))
					defer.resolve({ posts: [], trello: [] });
				else {
					var promises = _.map($scope.attachments, function (append) {
						var file = append.file;
						var thumbnail = null;
						if (append.type == 'image' || append.type == 'video' ||
							(append.type == 'application' && append.subtype == 'pdf')) {
							thumbnail = append.thumbnail;
						}
						var deferred = $q.defer();
						// Upload Files and thumbnails
						DataService.UploadFiles({ file: file, thumbnail: thumbnail })
							.then(function (response) {
								console.log(response);
								var post = {
									date: (new Date()).toISOString(),
									user: $scope.activity.user,
									comment: append.comment,
									attachment: response.attachment,
									thumbnail: response.thumbnail
								};
								var trello = {
									'name': response.attachment['filename'],
									'url': response.attachment['file']['url'],
									'comment': append.comment
								};
								deferred.resolve({ post: post, trello: trello });
							});
						return deferred.promise;
					});
					// Update Activity with uploaded files
					$q.all(promises).then(function (response) {
						var trello = [];
						var posts = _.map(response, function (resp) {
							trello.push(resp.trello);
							return resp.post;
						});
						defer.resolve({ posts: posts, trello: trello });
					});
				}
				return defer.promise;
			};
		}])


	.filter('unsafe', ['$sce', function ($sce) {
		return $sce.trustAsHtml;
	}])
