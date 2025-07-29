# Document contents

Each document is written in Markdown and can make use of several markdown extensions, already installed in the default configuration.

## Installed markdown extensions

Projects generated with the Wolf Project Generator come with a set of useful markdown extensions already installed and ready for use. Shown here
is the list of those extensions and short examples of how to use them.

For the complete list of available extensions see [The Pymdown-extensions Documentation](https://facelessuser.github.io/pymdown-extensions/)

- Emoji. Writting for example `:cloud:` you get :cloud:. Some useful ones

  :star: :boom: :question: :+1: :-1: :point_right: :skull: :eyes: :thought_balloon: :cloud: :zap: :envelope: :lock: :key: :mag: :computer: :watch: :file_folder: :pencil: :bookmark: :memo: :book: :warning: :ok: :no_entry: :x: :red_circle:

  (hover to see its textual form). A complete list can be found [here](https://gist.github.com/rxaviers/7360908). All these emoji are converted by the default settings to PNG, so that they will look the same in any browser/operating system.

- [Keys](https://facelessuser.github.io/pymdown-extensions/extensions/keys/), to typeset keystrokes; `++ctrl+c++` --> ++ctrl+c++
- Tilde, allows `~~strikethrough~~`, for ~~example~~.
- Mark, allows to `==highlight==` ==like this==.
- Smartsymbols, among other, it allows to typeset `-->` or `1/2` to get --> or 1/2.
- Superfences. Expands the possibilities of code fragment, allowing for marking lines, numbering, grouping listings in tabs, etc. It also allows those code fragments to be used inside other nested environments, such as quotes, admonitions or details (see later), as well as item lists, enumerations, etc.

  ````markdown
  === "Python example"

      ```python linenums="1" hl_lines="2"
      # Hello world in python
      print("Hello world")
      ```

  === "C example"

      ```c linenums="1" hl_lines="5"
      // Hola mundo en C
      #include<stdio.h>
      int main()
      {
          printf("Hello world\n");
          return 0;
      }
      ```
  ````

  === "Python example"

        ```python linenums="1" hl_lines="2"
        # Hello world in python
        print("Hello world")
        ```

  === "C example"

        ```c linenums="1" hl_lines="5"
        // Hola mundo en C
        #include<stdio.h>
        int main()
        {
            printf("Hello world\n");
            return 0;
        }
        ```

---

- Admonitions like this one:

  ```markdown
  !!! danger "Warning"
  This can be written like this:

  [...]
  ```

  !!! danger "Warning"
  This can be written like this:

---

- Details, which allows for collapsable blocks, which can be written like this:

  ```markdown
  ??? info "Listing of all admonition/details types"
  This part is hidden until clicking in the header. You can use `???+` instead of
  `???` to cause an expanded initial state.

  !!! example

  !!! quote

  !!! abstract

  !!! info

  !!! tip

  !!! done

  !!! question

  !!! warning

  !!! fail

  !!! danger

  !!! bug
  ```

  Which produces:

  ???+ info "Listing of all admonition/details types (click on the caret > to toggle expanding . . .)"

        !!! example

        !!! quote

        !!! abstract

        !!! info

        !!! tip

        !!! done

        !!! question

        !!! warning

        !!! fail

        !!! danger

        !!! bug

---

- ProgressBar, which can be useful to show the percentage of the paper/book while reading it. For example:

  ```markdown
  [=65% "65%"]
  ```

  [=65% "65%"]

---

- Tasklist, which styles to-do lists, like the following one:

  ```markdown
  Finished

          - [X] Introduction
          - [ ] State of the art
          - [X] Model
          - [X] Experiments
          - [ ] Conclusions
  ```

  ???+ example "To-do list example"

        Finished

        - [X] Introduction
        - [ ] State of the art
        - [X] Model
        - [X] Experiments
        - [ ] Conclusions
