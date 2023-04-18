'use strict';

angular.module('suporte.services', [
	'auth.service',
	'data.service',
	'notifiy.factory',
	'dlg.confirm.service',
	'modal.page.service'
	// 'bid.notifiy.service',
	// 'pager.service'
])

	// .factory('sse', ['$rootScope', function($rootScope) {
	// 	return {
	// 		addEventListener: function(eventName, callback) {
	// 			var sse = new EventSource('/events');
	// 			sse.addEventListener(eventName, function() {
	// 				var args = arguments;
	// 				$rootScope.$apply(function () {
	// 					console.log(sse);
	// 					console.log(args);
	// 					callback.apply(sse, args);
	// 				});
	// 			});
	// 		}
	// 	};
	// }])
	.factory('sse', ['$rootScope', function ($rootScope) {
		var sse = new EventSource('/events');
		return {
			addEventListener: function (eventName, callback) {
				sse.addEventListener(eventName, function () {
					var args = arguments;
					$rootScope.$apply(function () {
						callback.apply(sse, args);
					});
				});
			}
		};
	}])


	.factory('toClipboard', ['$compile', '$rootScope', '$document', function ($compile, $rootScope, $document) {
		return {
			copy: function (element) {
				var copyElement = angular.element('<span id="ngClipboardCopyId">' + element + '</span>');
				var body = $document.find('body').eq(0);
				body.append($compile(copyElement)($rootScope));

				var ngClipboardElement = angular.element(document.getElementById('ngClipboardCopyId'));
				var range = document.createRange();

				range.selectNode(ngClipboardElement[0]);

				window.getSelection().removeAllRanges();
				window.getSelection().addRange(range);

				var successful = document.execCommand('copy');

				var msg = successful ? 'successful' : 'unsuccessful';
				window.getSelection().removeAllRanges();

				copyElement.remove();
			}
		}
	}])

	.factory('httpInterceptor', ['$q', '$injector', '$timeout', 'PROXIMIDADE_SUPORTE_URLS', function ($q, $injector, $timeout, PROXIMIDADE_SUPORTE_URLS) {
		return {
			'request': function (config) {
				return config;
			},
			'requestError': function (rejection) {
				// console.log('requestError');
				// console.log(rejection);
				return $q.reject(rejection);
			},
			'response': function (response) {
				return response;
			},
			'responseError': function (rejection) {
				// console.log('responseError');
				// console.log(rejection);
				if (rejection.data === null && rejection.status == -1) {
					var notify = $injector.get('Notify');
					if (notify) {
						notify.info({
							title: 'Falha na Autenticação',
							message: 'Usuário não autenticado. Por favor, faça o login novamente.',
							position: 'right',
							duration: 3000,
							container: angular.element(document.querySelector("#id_notify"))
						});
					}
					$timeout(function () {
						$injector.get('$window').open(PROXIMIDADE_SUPORTE_URLS.unauthenticated, '_self');
					}, 3000);
				}
				return $q.reject(rejection);
			}
		};
	}])

	.config(['$httpProvider', function ($httpProvider) {
		$httpProvider.interceptors.push('httpInterceptor');
	}]);

