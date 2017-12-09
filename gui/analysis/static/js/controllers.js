angular.module('challengerApp.controllers', [])
  .controller('ExperimentController', function ($scope, $stateParams, $uibModal, ExperimentService, ExperimentServiceV2, NgTableParams, ExperimentCsvService, ExperimentStaticService, MetricService) {
    $scope.id = $stateParams.id
    $scope.experiment_v2 = ExperimentServiceV2.get({ id: $stateParams.id })
    $scope.experiment = ExperimentService.get({ id: $stateParams.id })
    $scope.perf_correlation = ExperimentCsvService.get({ id: $stateParams.id, csv: 'performance_corr.csv' })
    $scope.perf_pvalue = ExperimentCsvService.get({ id: $stateParams.id, csv: 'performance_p_values.csv' })
    $scope.anon_correlation = ExperimentCsvService.get({ id: $stateParams.id, csv: 'anonymity_corr.csv' })
    $scope.anon_pvalue = ExperimentCsvService.get({ id: $stateParams.id, csv: 'anonymity_p_values.csv' })
    $scope.graphs = { 'routing': [], 'graph': [], 'adversary': [], 'sender_set': [], 'anonymity_exponential_backoff': [], 'anonymity_actual_backoff': [] }
    $scope.can_show = function (items) {
      var result = {}
      angular.forEach(items, function (value, key) {
        if (!key.startsWith('_')) {
          result[key] = value
        }
      })
      return result
    }

    // load the routing choice graph data
    MetricService.get({ id: $stateParams.id, metric: 'stats.json' }).$promise.then(function (result) {
      result.options = stacked_graph_options('Routing Preferences Taken: Stacked')
      result.type = 'line'
      $scope.graphs['routing'].push(result)
    })

    // load the routing choice graph data
    MetricService.get({ id: $stateParams.id, metric: 'path_histo.json' }).$promise.then(function (result) {
      result.options = basic_graph_options('Path Lengths (Hops): Histogram')
      result.type = 'bar'
      $scope.graphs['routing'].push(result)
    })

    // load the intercept hop graph data
    MetricService.get({ id: $stateParams.id, metric: 'intercept.json' }).$promise.then(function (result) {
      result.options = basic_graph_options('Adversary Intercept at Hop: Histogram')
      result.type = 'bar'
      $scope.graphs['adversary'].push(result)
    })

    // load the intercept hop graph data
    MetricService.get({ id: $stateParams.id, metric: 'intercept_calculated.json' }).$promise.then(function (result) {
      result.options = basic_graph_options('Adversary Intercept at Hop for Calculated: Histogram')
      result.type = 'bar'
      $scope.graphs['adversary'].push(result)
    })

    MetricService.get({ id: $stateParams.id, metric: 'intercept_percent.json' }).$promise.then(function (result) {
      result.options = basic_graph_options('Adversary Intercept Percent at Hop: Sumation')
      result.type = 'line'
      $scope.graphs['adversary'].push(result)
    })

    // load the sender set graph data
    MetricService.get({ id: $stateParams.id, metric: 'sender_set_size.json' }).$promise.then(function (result) {
      result.options = basic_graph_options('Sender Set Size: Histogram')
      result.type = 'bar'
      $scope.graphs['sender_set'].push(result)
    })

    // load the sender set by intercept hop graph data
    MetricService.get({ id: $stateParams.id, metric: 'sender_set_size_by_hop.json' }).$promise.then(function (result) {
      result.options = basic_graph_options('Sender Set Size by Intercepted at Hop: Average')
      result.type = 'line'
      $scope.graphs['sender_set'].push(result)
    })

    // load the entropy graph data
    MetricService.get({ id: $stateParams.id, metric: 'entropy.json' }).$promise.then(function (result) {
      result.options = basic_graph_options('Entropy: Histogram')
      result.type = 'bar'
      $scope.graphs['anonymity_exponential_backoff'].push(result)
    })

    MetricService.get({ id: $stateParams.id, metric: 'entropy_normalized.json' }).$promise.then(function (result) {
      result.options = basic_graph_options('Entropy Normalized: Histogram')
      result.type = 'bar'
      $scope.graphs['anonymity_exponential_backoff'].push(result)
    })

    // load the sender set by intercept hop graph data
    MetricService.get({ id: $stateParams.id, metric: 'entropy_by_hop.json' }).$promise.then(function (result) {
      result.options = basic_graph_options('Entropy by Intercepted at Hop: Average')
      result.type = 'line'
      $scope.graphs['anonymity_exponential_backoff'].push(result)
    })
    MetricService.get({ id: $stateParams.id, metric: 'entropy_normalized_by_hop.json' }).$promise.then(function (result) {
      result.options = basic_graph_options('Entropy Normalized by Intercepted at Hop: Average')
      result.type = 'line'
      $scope.graphs['anonymity_exponential_backoff'].push(result)
    })

    MetricService.get({ id: $stateParams.id, metric: 'top_rank_set_size_by_hop.json' }).$promise.then(function (result) {
      result.options = basic_graph_options('Top Ranked Sender Set Size by Intercepted at Hop: Average')
      result.type = 'line'
      $scope.graphs['anonymity_exponential_backoff'].push(result)
    })

    MetricService.get({ id: $stateParams.id, metric: 'top_rank_by_hop.json' }).$promise.then(function (result) {
      result.options = basic_graph_options('Top Ranked Value by Intercepted at Hop: Average')
      result.type = 'line'
      $scope.graphs['anonymity_exponential_backoff'].push(result)
    })

    // load the entropy graph data
    MetricService.get({ id: $stateParams.id, metric: 'entropy_actual.json' }).$promise.then(function (result) {
      result.options = basic_graph_options('Entropy: Histogram')
      result.type = 'bar'
      $scope.graphs['anonymity_actual_backoff'].push(result)
    })

    MetricService.get({ id: $stateParams.id, metric: 'entropy_normalized_actual.json' }).$promise.then(function (result) {
      result.options = basic_graph_options('Entropy Normalized: Histogram')
      result.type = 'bar'
      $scope.graphs['anonymity_actual_backoff'].push(result)
    })

    // load the sender set by intercept hop graph data
    MetricService.get({ id: $stateParams.id, metric: 'entropy_by_hop_actual.json' }).$promise.then(function (result) {
      result.options = basic_graph_options('Entropy by Intercepted at Hop: Average')
      result.type = 'line'
      $scope.graphs['anonymity_actual_backoff'].push(result)
    })

    MetricService.get({ id: $stateParams.id, metric: 'entropy_normalized_by_hop_actual.json' }).$promise.then(function (result) {
      result.options = basic_graph_options('Entropy Normalized by Intercepted at Hop: Average')
      result.type = 'line'
      $scope.graphs['anonymity_actual_backoff'].push(result)
    })


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
        templateUrl: 'myModalContentCvs.html',
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
