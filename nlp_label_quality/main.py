from nlp_label_quality.controller.controller import TkEventController
from nlp_label_quality.view.view import TkView
from nlp_label_quality.model.model import TkDataModel


if __name__ == '__main__':
    # create the MVC & start the application
    model = TkDataModel()
    view = TkView()
    c = TkEventController(model, view)
    c.start()
