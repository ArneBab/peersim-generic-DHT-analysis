angular.module('challengerApp.controllers', [])
  .controller('ExperimentController', function ($scope, $stateParams, $uibModal, ExperimentService, ExperimentServiceV2, ExperimentCsvService, ExperimentStaticService, MetricService) {
    $scope.id = $stateParams.id
    $scope.experiment_v2 = ExperimentServiceV2.get({ id: $stateParams.id })

    $scope.open = function (graph_data) {
      var modalInstance = $uibModal.open({
        animation: true,
        ariaLabelledBy: 'modal-title',
        ariaDescribedBy: 'modal-body',
        templateUrl: 'myModalContent.html',
        controller: 'ModalInstanceCtrl',
        controllerAs: '$ctrl',
        size: 'lg',
        resolve: {
          data: function () {
            return graph_data
          }
        }
      })
    }

    $scope.open_csv = function (cvs_data) {
      var modalInstance = $uibModal.open({
        animation: true,
        ariaLabelledBy: 'modal-title',
        ariaDescribedBy: 'modal-body',
        templateUrl: 'myModalContentCsv.html',
        controller: 'ModalInstanceCtrl',
        controllerAs: '$ctrl',
        size: 'lg',
        resolve: {
          data: function () {
            var parsed = cvs_data.split('\n')
            var data = []
            for(var i = 1; i < parsed.length; i++){
              var line = parsed[i]
              if(!line) continue
              data.push(line.split(','))
            }
            return {headers: parsed[0].split(','), body: data}
          }
        }
      })
    }

    $scope.download_csv = function (name, cvs_data) {
      var a = angular.element('<a></a>');
      a.attr('href','data:application/octet-stream;base64,' + btoa(cvs_data))
      a.attr('style', 'display:none')
      a.attr('download', name + '.csv');
      a[0].click()
      a.remove();
    }

  }).controller('ModalInstanceCtrl', function ($uibModalInstance, data) {
    var $ctrl = this
    $ctrl.data = data
    $ctrl.ok = function () {
      $uibModalInstance.close()
    }
  })
  .controller('SummaryController', function ($scope, $uibModal, SummaryService, SummaryGraphService) {
    $scope.graphs = SummaryGraphService.query()
    $scope.summary = SummaryService.query()
    $scope.open = function (graph_data) {
      var modalInstance = $uibModal.open({
        animation: true,
        ariaLabelledBy: 'modal-title',
        ariaDescribedBy: 'modal-body',
        templateUrl: 'myModalContent.html',
        controller: 'ModalInstanceCtrl',
        controllerAs: '$ctrl',
        size: 'lg',
        resolve: {
          graph: function () {
            return graph_data
          }
        }
      })
    }
  })
  .controller('VariableController', function ($scope, $stateParams, $uibModal, SummaryGraphService, SummaryCorrelationService) {
    $scope.id = $stateParams.id
    $scope.graphs = SummaryGraphService.get({ variable: $stateParams.id })
    $scope.correlations = SummaryCorrelationService.get({ variable: $stateParams.id })
    $scope.open = function (graph_data) {
      var modalInstance = $uibModal.open({
        animation: true,
        ariaLabelledBy: 'modal-title',
        ariaDescribedBy: 'modal-body',
        templateUrl: 'myModalContent.html',
        controller: 'ModalInstanceCtrl',
        controllerAs: '$ctrl',
        size: 'lg',
        resolve: {
          graph: function () {
            return graph_data
          }
        }
      })
    }
  })
  .controller('MenuController', function ($scope, $state, ExperimentService) {
    ExperimentService.query().$promise.then(function (result) {
      $scope.tree.push({ label: 'Summary', children: [], data: '/#/' })
      $scope.tree.push({ label: 'Variables', children: result.variables })
      $scope.tree.push({ label: 'Experiments', children: result.experiments })
    })
    $scope.tree = []
    $scope.tree_handler = function (branch) {
      if (branch.data)
        window.location.href = branch.data
      //$state.go('experiments_view', { id: branch.data.id })
    }
  }).controller('DataController', function ($scope, $state, $stateParams, DataService) {
    $scope.id = $stateParams.id
    $scope.filter_text = ''
    $scope.filtered_data = []
    $scope.on_filter = function () {
      $scope.filtered_data = { 'status': 'Loading....' }
      DataService.query({ id: $stateParams.id, filter: $scope.filter_text }).$promise.then(function (result) {
        $scope.filtered_data = result.items
      })
    }
  })

function basic_graph_options(title) {
  return {
    title: {
      display: true,
      text: title
    },
    responsive: true,
    legend: {
      display: false
    },
    elements: { line: { fill: false } }
  }
}

function stacked_graph_options(title) {
  return {
    title: {
      display: true,
      text: title
    },
    responsive: true,
    elements: { line: { fill: false } },
    scales: {
      yAxes: [
        {
          stacked: true
        }
      ]
    }
  }
}
