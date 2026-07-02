import magnetic from './magnetic'
import spotlight from './spotlight'
import fadeIn from './fadeIn'
import countUp from './countUp'
import ripple from './ripple'

export function registerDirectives(app) {
  app.directive('magnetic', magnetic)
  app.directive('spotlight', spotlight)
  app.directive('fade-in', fadeIn)
  app.directive('count-up', countUp)
  app.directive('ripple', ripple)
}

export { magnetic, spotlight, fadeIn, countUp, ripple }
