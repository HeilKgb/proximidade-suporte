/* jshint unused:vars */
'use strict';

var app = angular.module('suporte', ['ngInputModified', 'ngFileUpload', 'ngAnimate', 'ngSanitize',
	'ngMessages', 'ngCookies', 'ui.router', 'ui.router.state.events', 'cgNotify', 'ui.select', 'ui.bootstrap',
	'angular-loading-bar', 'ngStorage', 'ui.utils.masks', 'angularBootstrapMaterial', 'mgcrea.ngStrap.tooltip',
	'ui.bootstrap.datetimepicker', 'linkify', 'panzoom', 'panzoomwidget',
	'suporte.controllers', 'suporte.directives', 'suporte.services']);


app.constant('uiDatetimePickerConfig', {
	dateFormat: 'yyyy-MM-dd HH:mm',
	defaultTime: '00:00:00',
	html5Types: { date: 'yyyy-MM-dd', 'datetime-local': 'yyyy-MM-ddTHH:mm:ss.sss', 'month': 'yyyy-MM' },
	initialPicker: 'date',
	reOpenDefault: false,
	enableDate: true,
	enableTime: true,
	buttonBar: {
		show: true,
		now: { show: true, text: 'Agora', cls: 'btn-sm btn-default' },
		today: { show: true, text: 'Hoje', cls: 'btn-sm btn-default' },
		clear: { show: true, text: 'Limpar', cls: 'btn-sm btn-default' },
		date: { show: true, text: 'Data', cls: 'btn-sm btn-default' },
		time: { show: true, text: 'Hora', cls: 'btn-sm btn-default' },
		close: { show: true, text: 'Fechar', cls: 'btn-sm btn-default' },
		cancel: { show: false, text: 'Cancelar', cls: 'btn-sm btn-default' }
	},
	closeOnDateSelection: true,
	closeOnTimeNow: true,
	appendToBody: false,
	altInputFormats: [],
	ngModelOptions: {},
	saveAs: false,
	readAs: false
});

app.constant('PROXIMIDADE_SUPORTE_URLS', {
	domain: api_settings.domain,
	dash_app: api_settings.dash_app,
	profile_url: api_settings.user_manager,
	user_manager_token: api_settings.user_manager + '/#/?continue=' + api_settings.main_app,
	admin: api_settings.admin,
	unauthenticated: api_settings.authcenter + '/#/login?continue=' + api_settings.main_app,
	images: api_settings.images,
	main_app: api_settings.main_app
});

app.constant('APP_CONSTANTS', {
	token: 'appKey'
});

app.constant('AUTH_EVENTS', {
	loginSuccess: 'auth-login-success',
	loginFailed: 'auth-login-failed',
	logoutSuccess: 'auth-logout-success',
	sessionTimeout: 'auth-session-timeout',
	notAuthenticated: 'auth-not-authenticated',
	notAuthorized: 'auth-not-authorized',
	Authenticated: 'auth-authenticated'
});

app.constant('USER_ROLES', {
	all: ['Administrator', 'Advanced User', 'User'],
	supports: ['Administrator', 'Advanced User'],
	admin: 'Administrator',
	advuser: 'Advanced User',
	user: 'User'
});

// app.run(['$trace', function($trace) {
// 	$trace.enable('TRANSITION');
// }]);

app.run(['$rootScope', '$state', '$transitions', '$window', 'AUTH_EVENTS', 'PROXIMIDADE_SUPORTE_URLS',
	function ($rootScope, $state, $transitions, $window, AUTH_EVENTS, PROXIMIDADE_SUPORTE_URLS) {

		$rootScope.$state = $state;

		//===== History
		$rootScope.history = [];
		$rootScope.Previous = null;
		$transitions.onSuccess({}, function (transition) {
			const params = Object.assign({}, transition.params());
			var label = ('data' in transition.to() && 'nome' in transition.to()['data']) ? transition.to()['data']['nome'] : transition.to().name;
			var previous = $rootScope.history.length ? $rootScope.history.slice(-1)[0]['label'] : undefined;
			$rootScope.history.push({ name: transition.to().name, params: params, label: label });
			$rootScope.Previous = previous;
		});
		$rootScope.goBack = function () {
			var prevUrl = $rootScope.history.length > 1 ? $rootScope.history.splice(-2)[0] : { name: 'main', params: {} };
			$state.go(prevUrl.name, prevUrl.params);
		};
		//===== History

		$transitions.onBefore({}, function (transition) {
			// console.log('onBefore from:', transition.from().name, ' to:', transition.to().name)
			var AuthService = transition.injector().get('AuthService');
			AuthService.CheckAuthenticated().then(function (response) {
				$rootScope.$broadcast(AUTH_EVENTS.Authenticated);
				return true;
			}, function (error) {
				// console.log('not Authenticated');
				$rootScope.$broadcast(AUTH_EVENTS.notAuthenticated);
				$window.open(PROXIMIDADE_SUPORTE_URLS.unauthenticated, '_self');
				return false;
			});
		});

		$transitions.onBefore({}, function (transition) {
			// console.log('onBefore criteriaRole from:', transition.from().name, ' to:', transition.to().name)
			const authorizedRoles = transition.to().data.authorizedRoles;
			if (!angular.isArray(authorizedRoles))
				authorizedRoles = [authorizedRoles];
			return fetch('/auth/user/role')
				.then(resp => resp.json())
				.then(data => {
					if (authorizedRoles.indexOf(data['role']) === -1) {
						$rootScope.$broadcast(AUTH_EVENTS.notAuthorized);
						return transition.router.stateService.target('main');
					}
					else {
						return true;
					}
				})
				.catch((error) => {
					console.error('Error:', error);
					$window.open(PROXIMIDADE_SUPORTE_URLS.unauthenticated, '_self');
					return false;
				});
		});

		$state.defaultErrorHandler(function (error) {
			console.log(error);
		});
	}]);

app.config(['$urlMatcherFactoryProvider', function ($urlMatcherFactory) {
	$urlMatcherFactory.type("ObjParam", {
		decode: function (val) { return typeof (val) === "string" ? JSON.parse(val) : val; },
		encode: function (val) { return JSON.stringify(val); },
		equals: function (a, b) { return this.is(a) && this.is(b); },
		is: function (val) { return angular.isObject(val); }
	});
}]);

app.config(['$stateProvider', '$urlRouterProvider', 'USER_ROLES', 'PROXIMIDADE_SUPORTE_URLS',
	function ($stateProvider, $urlRouterProvider, USER_ROLES, PROXIMIDADE_SUPORTE_URLS) {

		$stateProvider
			.state('main', {
				url: '/',
				controller: 'ActivitiesCtrl',
				controllerAs: 'ctrl',
				templateUrl: 'activities.html',
				data: {
					authorizedRoles: USER_ROLES.all
				},
				resolve: {
					apps_data: ['DataService', function (DataService) {
						return DataService.GetApplications({ method: 'GET', url: '/applications' });
					}],
					lt_data: ['DataService', function (DataService) {
						return DataService.GetLTData({ method: 'GET', url: '/activities' });
					}],
				}
			})
			.state('solicitacao', {
				controller: 'TimelineCtrl',
				controllerAs: 'ctrlTl',
				templateUrl: 'timeline.html',
				params: {
					id: null,
				},
				data: {
					authorizedRoles: USER_ROLES.all
				},
				resolve: {
					current_user: ['AuthService', function (AuthService) {
						return AuthService.GetUser();
					}],
				}
			})

			.state('about', {
				url: '/about',
				templateProvider: ['$timeout', function ($timeout) {
					return $timeout(function () {
						return '<p class="lead">Suporte PROX</p><ul>' +
							'<li><a href="' + PROXIMIDADE_SUPORTE_URLS.main_app + '">Suporte PROX Web Site</a></li>' +
							'</ul>';
					}, 100);
				}],
				data: {
					authorizedRoles: USER_ROLES.all
				}
			});

		$urlRouterProvider.otherwise('/');
	}]);

app.config(['$httpProvider', function ($httpProvider) {
	$httpProvider.useApplyAsync(true);
}]);

app.config(['$locationProvider', function ($locationProvider) {
	$locationProvider.hashPrefix('');
	$locationProvider.html5Mode(false);
}]);

app.config(['cfpLoadingBarProvider', function (cfpLoadingBarProvider) {
	cfpLoadingBarProvider.includeSpinner = false;
}]);

app.config(['$compileProvider', function ($compileProvider) {
	$compileProvider.debugInfoEnabled(false);
}]);

