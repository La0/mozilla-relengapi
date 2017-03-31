module App.Merges exposing (..)

import Html exposing (..)
import Html.Attributes exposing (..)
import Http
import Html.Events exposing (onClick, onInput, onSubmit)
import Json.Decode as Json exposing (Decoder)
import Utils exposing (onChange, decodeJsonString)
import Dialog
import Hawk
import RemoteData as RemoteData exposing (WebData, RemoteData(Loading, Success, NotAsked, Failure), isSuccess)
import TaskclusterLogin as User


type Msg
    = Cancel
    | LoadMerges Int
    | LoadedMerges (WebData String)
      -- Hawk Extension
    | HawkRequest Hawk.Msg


type alias Model =
    { merges : WebData (List MergeTest)
    ,  bugzilla_id : Maybe Int
    , backend_uplift_url : String
    }


type alias MergeTest =
    { group : Int
    , revision : String
    , revision_parent : String
    , branch : String
    , status : String
    , message : String
    , created : String
    }


init : String -> ( Model, Cmd Msg )
init backend_uplift_url =
    ( 
      { merges = NotAsked
      , bugzilla_id = Nothing
      , backend_uplift_url = backend_uplift_url
      }
    , Cmd.none
    )


update : Msg -> Model -> User.Model -> ( Model, Cmd Msg )
update msg model user =
    case msg of
        HawkRequest hawkMsg ->
            ( model, Cmd.none )

        LoadMerges bugzilla_id ->
            ( { model | merges = Loading, bugzilla_id = Just bugzilla_id }
            -- Start loading all merges test for this bug
            , loadMerges model user bugzilla_id
            )

        LoadedMerges response ->
            ( { model | merges = decodeJsonString decodeMerges response }
            , Cmd.none
            )

        Cancel ->
            ( { model | merges = NotAsked, bugzilla_id = Nothing }
            , Cmd.none
            )

loadMerges : Model -> User.Model -> Int -> Cmd Msg
loadMerges model user bugzilla_id =
    -- Load all merge tests for a bug
    case user of
        Just credentials ->
            let
                url =
                    model.backend_uplift_url ++ "/bugs/" ++ (toString bugzilla_id) ++ "/patches"

                request =
                    Hawk.Request "Merges" "GET" url [] Http.emptyBody
            in
                Cmd.map HawkRequest
                    (Hawk.send request credentials)

        Nothing ->
            -- No credentials
            Cmd.none



-- Decode from json api


decodeMerges: Decoder (List MergeTest)
decodeMerges =
    Json.list decodeMerge

decodeMerge: Decoder MergeTest
decodeMerge = 
    Json.map7 MergeTest
        (Json.field "group" Json.int)
        (Json.field "revision" Json.string)
        (Json.field "revision_parent" Json.string)
        (Json.field "branch" Json.string)
        (Json.field "status" Json.string)
        (Json.field "message" Json.string)
        (Json.field "created" Json.string)


-- Display modal when a bug is selected


viewModal : Model -> Html Msg
viewModal model =
    Dialog.view
        (case model.bugzilla_id of
            Just bugzilla_id ->
                Just (dialogConfig bugzilla_id model.merges)

            Nothing ->
                Nothing
        )



-- Modal configuration to edit a contributor


dialogConfig : Int -> WebData (List MergeTest) -> Dialog.Config Msg
dialogConfig bugzilla_id merges =
    { closeMessage = Just Cancel
    , containerClass = Nothing
    , header = Just (h3 [] [ text ("Merge tests for #" ++ (toString bugzilla_id)) ])
    , body =
        Just
            (div []
                [ viewMergeTests merges
                ]
            )
    , footer =
        Just
            (div []
                [ button
                    [ class "btn"
                    , onClick Cancel
                    ]
                    [ text "Cancel" ]
                ]
            )
    }


viewMergeTests : WebData (List MergeTest) -> Html Msg
viewMergeTests merges =
    div [ class "row" ]
        [ div [ class "col-xs-12" ]
            [ case merges of
                NotAsked ->
                    span [] []

                Loading ->
                    div [ class "alert alert-info" ] [ text "Loading..." ]

                Failure f ->
                    div [ class "alert alert-danger" ] [ text ("Failure: " ++ (toString f)) ]

                Success merges_ ->
                    table [class "table table-striped"] ([
                      tr [] [
                        th [] [text "Revision"]
                        , th [] [text "Group"]
                        , th [] [text "Status"]
                        , th [] [text "Created"]
                      ]]
                      ++ (List.map viewMergeTest merges_)) 
            ]
        ]

viewMergeTest : MergeTest -> Html Msg
viewMergeTest merge =
    tr [ ] [
      td [] [text merge.revision],
      td [] [text (toString merge.group)],
      td [] [text (toString merge.status)],
      td [] [text (toString merge.created)]
    ]
