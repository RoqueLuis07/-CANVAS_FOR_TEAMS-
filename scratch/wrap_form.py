import os

with open('Frontend/templates/ingreso.html', 'r', encoding='utf-8') as f:
    content = f.read()

start_wrapper = """
        <!-- Accordion Creación Individual -->
        <div class="accordion mb-4" id="accordionIndividual">
          <div class="accordion-item border-info shadow-sm">
            <h2 class="accordion-header" id="headingIndividual">
              <button class="accordion-button fw-bold text-dark" type="button" data-bs-toggle="collapse" data-bs-target="#collapseIndividual" aria-expanded="true" aria-controls="collapseIndividual" style="background: linear-gradient(135deg, rgba(6, 182, 212, 0.1), rgba(8, 145, 178, 0.1));">
                <i class="bi bi-person-plus-fill me-2 text-info"></i> Creación Individual
              </button>
            </h2>
            <div id="collapseIndividual" class="accordion-collapse collapse show" aria-labelledby="headingIndividual" data-bs-parent="#accordionIndividual">
              <div class="accordion-body p-4">
        <form id="crearIndForm" onsubmit="event.preventDefault(); doCrearInd();">
"""
# Note: I set aria-expanded="true" and added class="show" to make it default-opened, just like a normal form would be, so they don't have to click it to see it. Actually, wait. The user explicitly said: "tambien conviertelo en un modal igual que los otros" referring to the accordion. If the others are collapsed by default, maybe they want this one collapsed too?
# But if it's collapsed, the whole page will be empty except the header and the accordions. I think I'll make it collapsed just like the others so it's consistent.

start_wrapper = """
        <!-- Accordion Creación Individual -->
        <div class="accordion mb-4" id="accordionIndividual">
          <div class="accordion-item border-info shadow-sm">
            <h2 class="accordion-header" id="headingIndividual">
              <button class="accordion-button collapsed fw-bold text-dark" type="button" data-bs-toggle="collapse" data-bs-target="#collapseIndividual" aria-expanded="false" aria-controls="collapseIndividual" style="background: linear-gradient(135deg, rgba(6, 182, 212, 0.1), rgba(8, 145, 178, 0.1));">
                <i class="bi bi-person-plus-fill me-2 text-info"></i> Creación Individual
              </button>
            </h2>
            <div id="collapseIndividual" class="accordion-collapse collapse" aria-labelledby="headingIndividual" data-bs-parent="#accordionIndividual">
              <div class="accordion-body p-4">
        <form id="crearIndForm" onsubmit="event.preventDefault(); doCrearInd();">
"""

content = content.replace('<form id="crearIndForm" onsubmit="event.preventDefault(); doCrearInd();">', start_wrapper)

end_target = '<div id="crearIndResult" class="mt-4" style="display:none;"></div>'
end_wrapper = end_target + '\n              </div>\n            </div>\n          </div>\n        </div>'
content = content.replace(end_target, end_wrapper)

with open('Frontend/templates/ingreso.html', 'w', encoding='utf-8') as f:
    f.write(content)

print("Form wrapped in accordion.")
