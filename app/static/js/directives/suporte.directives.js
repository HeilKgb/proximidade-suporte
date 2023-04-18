'use strict';

angular.module('suporte.directives',[
	'dlg.confirm.directive',
	'add.activity.directive',
	'attach-files.directive',
	'edit-activity.directive'
	// 'append-file.directive',

])

.directive('onEnter', [ function () {
	return function (scope, element, attrs) {
		element.bind("keydown keypress", function (event) {
			if(event.which === 13) {
				scope.$apply(function (){
					scope.$eval(attrs.onEnter);
				});

				event.preventDefault();
			}
		});
	};
}])

.directive('autoResize', ['$timeout', function autoResize($timeout) {
	var directive = {
		restrict: 'A',
		link: function autoResizeLink(scope, element, attributes, controller) {

			element.css({ 'height': 'auto', 'overflow-y': 'hidden' });
			$timeout(function () {
				element.css('height', element[0].scrollHeight + 'px');
			}, 100);

			element.on('input', function () {
				element.css({ 'height': 'auto', 'overflow-y': 'hidden' });
				element.css('height', element[0].scrollHeight + 'px');

			});
		}
	};
	return directive;
}])

.directive('validationError', [function () {
	return {
		restrict: 'A',
		require: 'ngModel',
		link: function (scope, elem, attrs, ctrl) {
			scope.$watch(attrs['validationError'], function (errMsg) {
				if (elem[0] && elem[0].setCustomValidity) { // HTML5 validation
					elem[0].setCustomValidity(errMsg);
				}
				if (ctrl) { // AngularJS validation
					ctrl.$setValidity('validationError', errMsg ? false : true);
				}
			});
		}
	}
}])

.directive('contenteditable', ['$sce', function($sce) {
	return {
		restrict: 'A',
		require: '?ngModel',
		link: function(scope, element, attrs, ngModel) {
			if (!ngModel) return;
			ngModel.$render = function() {
				element.html($sce.getTrustedHtml(ngModel.$viewValue || ''));
			};
			element.on('blur keyup change', function() {
				scope.$evalAsync(read);
			});
			read();
			function read() {
				var html = element.html();
				if (attrs.stripBr && html === '<br>') {
					html = '';
				}
				ngModel.$setViewValue(html);
			}
		}
	};
}])

.directive('loadFilesOnChange', [ function() {
	return {
		restrict: 'A',
		scope: {
				 method:'&loadFilesOnChange'
		 },
		link: function (scope, element, attrs) {
			var onChangeFunc = scope.method();
			element.bind('change', function(event){
				var files = event.target.files;
				if(onChangeFunc)
					onChangeFunc(files);
				element.val(null);
			});
		}
	};
}]);
