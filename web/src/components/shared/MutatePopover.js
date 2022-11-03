import React from 'react';
import { useState, useEffect } from 'react';
import { CaptiveLogin } from "./CaptiveLogin"
import {
  Slider,
  SliderTrack,
  SliderFilledTrack,
  SliderThumb,
  SliderMark,
} from '@chakra-ui/react'
import {
  Modal,
  ModalOverlay,
  ModalContent,
  ModalHeader,
  ModalFooter,
  ModalBody,
  ModalCloseButton,
  useDisclosure,
  Tooltip
} from '@chakra-ui/react'

import {
  Box,
  Heading,
  Link,
  Checkbox,
  Image,
  IconButton,
  Text,
  Flex,
  Divider,
  HStack,
  Tag,
  Wrap,
  WrapItem,
  SpaceProps,
  useColorModeValue,
  Container,
  Code,
  VStack,
  Button,
  SimpleGrid,
  useToast,
  Switch,
  FormControl,
  FormLabel,
  FormHelperText,
  Popover,
  PopoverTrigger,
  PopoverAnchor,
  PopoverArrow,
  PopoverBody,
  PopoverContent,
  PopoverHeader,
  PopoverCloseButton,
  Input,
  Textarea,
  ButtonGroup,
  Select,
  NumberDecrementStepper,
  NumberIncrementStepper,
  NumberInput,
  NumberInputField,
  NumberInputStepper
} from '@chakra-ui/react';

import { VscSettings } from 'react-icons/vsc';
import { BsDice3 } from 'react-icons/bs';

export function MutatePopover(props) {
  const { isOpen, onOpen, onClose } = useDisclosure()
  const [showTooltip, setShowTooltip] = useState(false)
  const loginDisclosure = useDisclosure()
  let onOpen2 = loginDisclosure.onOpen
  let onClose2 = loginDisclosure.onClose
  let isOpen2 = loginDisclosure.isOpen
  let data = props.piece
  if(data && data.params && data.params.denoising_strength === undefined){
    data.params.denoising_strength = 0.75
  }
  let token = props.token
  let sh = localStorage.getItem("show-mutate-help");
  let bs = localStorage.getItem("batchsize-settings");
  let showhelp = (sh==='false')?false:true

  let pr = localStorage.getItem("private-settings");
  let privatesettings = (pr==='true')?true:false
  let batch_size = bs?parseInt(bs):5

  const [tags, setTags] = useState([]);
  const [batchSize, setBatchSize] = useState(batch_size);
  const [privateSettings, setPrivateSettings] = useState(privatesettings);
  const [show_help, setShowHelp] = useState(showhelp);
  const [piece] = useState(data?data:{params:{}})
  const [dataCopy, setDataCopy] = useState(data?data:{params:{}})
  const [button, setButton] = useState(null)
  const [isLoading, setIsLoading] = useState(false)
  const toast = useToast()

  const handleClick = ()=>{
    if(token){
      onOpen()
    }else{
      loginDisclosure.onOpen()
    }
  }

  useEffect(()=>{
    setTags([])
    // fetch(
    //   `${process.env.REACT_APP_api_url}/v3/tags`,
    //   {
    //     method: 'GET',
    //     headers: {
    //       'Content-Type': 'application/json',
    //       Authorization: `Bearer ${token}`,
    //     }
    //   }
    // )
    // .then((response) => {
    //   return response.json()
    // })
    // .then((data) => {
    //   setTags(data)
    // });
  },[])

  useEffect(() => {
    if(isOpen) return   // Otherwise it will keep messing with dialog box
    setDataCopy(JSON.parse(JSON.stringify(props.piece)))
    // console.log(props.piece.private)
    // console.log(dataCopy.private)
    if(!props.buttonText){
      setButton(
      <Tooltip hasArrow label="Create">
        <IconButton
          isRound
          isDisabled={isLoading}
          colorScheme={'blue'}
          size="md"
          onClick={handleClick}
          icon={<VscSettings />}
        />
      </Tooltip>)
    }else{
      setButton(<Tooltip hasArrow label="Create"><Button 
        colorScheme="green"
        variant={'outline'}
        minW={0}
        onClick={handleClick}>{props.buttonText}</Button>
      </Tooltip>)
    }
  }, [props]);

  // useEffect(() => {
  //   setDataCopy(JSON.parse(JSON.stringify(props.piece)))
  // },[])

  async function save() {
    try {
      // return
      setIsLoading(true)
      let j = JSON.parse(JSON.stringify(dataCopy))
      j.batch_size = batchSize
      j.parent_uuid = dataCopy.uuid
      if(j.params.img2img){
        j.params.img2img_source_uuid = dataCopy.uuid
      }
      const { success: mutateSuccess, results: results } = await fetch(
        `${process.env.REACT_APP_api_url}/v3/create/mutate`,
        {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            Authorization: `Bearer ${token}`,
          },
          body: JSON.stringify({ job: j }),
        }
      )
      .then((response) => {
        return response.json();
      })
      .then((data) => {
        toast({
          title: "Job Received"
        })
        onClose()
        return data;
      });

      if (mutateSuccess) {
        // if(mode==="mutate"){
        //   if(results){
        //     // console.log(results)
        //     navigate(`/myreviews/1`);
        //   }
        // }
        // if(mode==="edit"){
        //   navigate(`/piece/${results[0].uuid}`);
        // }
      }
      setIsLoading(false);
    } catch (error) {
      console.log('Unable to mutate.');
    }
  }

  return (
    <>
    {button}
    <CaptiveLogin disclosure={loginDisclosure}/>
    <Modal isOpen={isOpen} onClose={onClose} size={"5xl"}>
      <ModalOverlay bg='none'
        backdropFilter='auto'
        backdropInvert='10%'
        backdropBlur='10px'/>
      <ModalContent>
        <ModalHeader>Create</ModalHeader>
        <ModalCloseButton />
        {token && <>
        <ModalBody>
          <Image
            borderRadius="lg"
            src={`http://images.feverdreams.app/thumbs/512/${dataCopy.preferredImage || piece.uuid}.jpg`}
            alt={piece.uuid}
            objectFit="contain"
          />
          <Wrap>
            <WrapItem>
              <FormControl>
                <FormLabel htmlFor="batch_size">Batch Size</FormLabel>
                <NumberInput
                  id="batch_size"
                  value={batchSize}
                  min={1}
                  max={15}
                  clampValueOnBlur={true}
                  onChange={(value) => {
                    let bs = parseInt(value);
                    localStorage.setItem("batchsize-settings",bs)
                    setBatchSize(bs);
                  }}
                >
                  <NumberInputField />
                  <NumberInputStepper>
                    <NumberIncrementStepper />
                    <NumberDecrementStepper />
                  </NumberInputStepper>
                </NumberInput>
              </FormControl>
            </WrapItem>
            <WrapItem>
              <FormControl>
                  <FormLabel htmlFor="seed">Image Seed</FormLabel>
                  <HStack>
                  <NumberInput
                    id="seed"
                    value={dataCopy.params.seed}
                    min={-1}
                    max={2 ** 32}
                    clampValueOnBlur={true}
                    onChange={(value) => {
                      let updatedPiece = JSON.parse(JSON.stringify(dataCopy));
                      updatedPiece.params.seed = parseInt(value);
                      setDataCopy({ ...dataCopy, ...updatedPiece });
                    }}
                  >
                    <NumberInputField />
                    <NumberInputStepper>
                      <NumberIncrementStepper />
                      <NumberDecrementStepper />
                    </NumberInputStepper>
                  </NumberInput>
                  <IconButton
                    isRound
                    variant={"ghost"}
                    size="md"
                    onClick={() => {
                      let updatedPiece = JSON.parse(JSON.stringify(dataCopy))
                      let r = Math.floor(Math.random() * (2**32))
                      updatedPiece.params.seed = parseInt(r)
                      setDataCopy({ ...piece, ...updatedPiece })
                    }}
                    // ml={1}
                    icon={<BsDice3 />}
                  ></IconButton>
                  </HStack>
                </FormControl>
            </WrapItem>
            </Wrap>
            <Wrap>
            <WrapItem>
              <FormControl>
                <FormLabel htmlFor="private">Private Settings</FormLabel>
                <Switch
                  id="private"
                  isChecked={dataCopy.private}
                  onChange={(event) => {
                    setPrivateSettings(event.target.checked)
                    localStorage.setItem("private-settings",event.target.checked)
                    let updatedPiece = JSON.parse(JSON.stringify(dataCopy));
                    updatedPiece.private = event.target.checked ? true : false;
                    setDataCopy({ ...dataCopy, ...updatedPiece });
                  }}
                />
                {show_help && <FormHelperText>Keep settings private</FormHelperText>}
              </FormControl>
            </WrapItem>
            <WrapItem>
                <FormControl>
                <FormLabel htmlFor="img2img">img2img</FormLabel>
                <Switch
                    id="img2img"
                    isChecked = {dataCopy.params.img2img}
                    onChange={(event) => {
                      let img2img = event.target.checked
                      let updatedPiece = JSON.parse(JSON.stringify(dataCopy));
                      updatedPiece.params.img2img = img2img;
                      setDataCopy({ ...dataCopy, ...updatedPiece });
                    }}
                  />
              </FormControl>
            </WrapItem>
            <WrapItem>
                <FormControl>
                <FormLabel htmlFor="restore_faces">Restore Faces</FormLabel>
                <Switch
                    id="restore_faces"
                    isChecked = {dataCopy.params.restore_faces}
                    onChange={(event) => {
                      let restore_faces = event.target.checked
                      let updatedPiece = JSON.parse(JSON.stringify(dataCopy));
                      updatedPiece.params.restore_faces = restore_faces;
                      setDataCopy({ ...dataCopy, ...updatedPiece });
                    }}
                  />
              </FormControl>
            </WrapItem>
            {!dataCopy.params.img2img && <WrapItem>
                <FormControl>
                <FormLabel htmlFor="enable_hr">Highres. Fix</FormLabel>
                <Switch
                    id="enable_hr"
                    isChecked = {dataCopy.params.enable_hr}
                    onChange={(event) => {
                      let enable_hr = event.target.checked
                      let updatedPiece = JSON.parse(JSON.stringify(dataCopy));
                      updatedPiece.params.enable_hr = enable_hr;
                      setDataCopy({ ...dataCopy, ...updatedPiece });
                    }}
                  />
              </FormControl>
            </WrapItem>}
            
          </Wrap>
          {dataCopy.params.img2img && 
            <WrapItem>
              <FormControl>
                <FormLabel htmlFor="img2img_denoising_strength">img2img Denoising Strength ({dataCopy.params.img2img_denoising_strength || 0.75 })</FormLabel>
                <Slider
                    id='img2img_denoising_strength'
                    value={dataCopy.params.img2img_denoising_strength || 0.75}
                    step = {0.05}
                    min={0}
                    max={1}
                    // onChangeEnd={(v) => setSliderValue(v)}
                    onChange={(v) => {
                      let updatedPiece = JSON.parse(JSON.stringify(dataCopy))
                      updatedPiece.params.img2img_denoising_strength = parseFloat(v)
                      setDataCopy({ ...piece, ...updatedPiece })
                      // setSliderValue(v)
                    }}
                    onMouseEnter={() => setShowTooltip(true)}
                    onMouseLeave={() => setShowTooltip(false)}
                  >
                  <SliderMark value={25} mt='1' ml='-2.5' fontSize='sm'>
                    25%
                  </SliderMark>
                  <SliderMark value={50} mt='1' ml='-2.5' fontSize='sm'>
                    50%
                  </SliderMark>
                  <SliderMark value={75} mt='1' ml='-2.5' fontSize='sm'>
                    75%
                  </SliderMark>
                  <SliderTrack>
                    <SliderFilledTrack />
                  </SliderTrack>
                  <Tooltip
                    hasArrow
                    bg='blue.500'
                    color='white'
                    placement='top'
                    isOpen={showTooltip}
                    label={`${dataCopy.params.img2img_denoising_strength}%`}
                  >
                    <SliderThumb />
                  </Tooltip>
                </Slider>
                </FormControl>
            </WrapItem>}
          {!dataCopy.params.img2img && dataCopy.params.enable_hr && 
            <FormControl>
            <FormLabel htmlFor="denoising_strength">Denoising Strength ({dataCopy.params.denoising_strength})</FormLabel>
            <Slider
                id='denoising_strength'
                value={dataCopy.params.denoising_strength}
                step = {0.05}
                min={0}
                max={1}
                // onChangeEnd={(v) => setSliderValue(v)}
                onChange={(v) => {
                  let updatedPiece = JSON.parse(JSON.stringify(dataCopy))
                  updatedPiece.params.denoising_strength = parseFloat(v)
                  setDataCopy({ ...piece, ...updatedPiece })
                  // setSliderValue(v)
                }}
                onMouseEnter={() => setShowTooltip(true)}
                onMouseLeave={() => setShowTooltip(false)}
              >
              <SliderMark value={25} mt='1' ml='-2.5' fontSize='sm'>
                25%
              </SliderMark>
              <SliderMark value={50} mt='1' ml='-2.5' fontSize='sm'>
                50%
              </SliderMark>
              <SliderMark value={75} mt='1' ml='-2.5' fontSize='sm'>
                75%
              </SliderMark>
              <SliderTrack>
                <SliderFilledTrack />
              </SliderTrack>
              <Tooltip
                hasArrow
                bg='blue.500'
                color='white'
                placement='top'
                isOpen={showTooltip}
                label={`${dataCopy.params.denoising_strength}%`}
              >
                <SliderThumb />
              </Tooltip>
            </Slider>
            </FormControl>
          }
          <FormControl>
              <FormLabel htmlFor="prompt">Prompt</FormLabel>
              <Textarea
                id={`prompt`}
                type="text"
                value={dataCopy.params.prompt}
                onChange={(event) => {
                  let prompt = event.target.value
                  let updatedPiece = JSON.parse(JSON.stringify(dataCopy));
                  updatedPiece.params.prompt = prompt;
                  setDataCopy({ ...dataCopy, ...updatedPiece });
                }}
              />
          </FormControl>
          <FormControl>
              <FormLabel htmlFor="negative_prompt">Negative Prompt</FormLabel>
              <Textarea
                id={`negative_prompt`}
                type="text"
                value={dataCopy.params.negative_prompt}
                onChange={(event) => {
                  let negative_prompt = event.target.value
                  let updatedPiece = JSON.parse(JSON.stringify(dataCopy));
                  updatedPiece.params.negative_prompt = negative_prompt;
                  setDataCopy({ ...dataCopy, ...updatedPiece });
                }}
              />
          </FormControl>
          <Wrap>
            <WrapItem>
              <FormControl>
                <FormLabel htmlFor="sampler">Sampler</FormLabel>
                <Select id = "sampler" value={dataCopy.params.sampler} onChange={(event) => {
                    let updatedPiece = JSON.parse(JSON.stringify(dataCopy));
                    let value = event.target.selectedOptions[0].value;
                    updatedPiece.params.sampler = value
                    setDataCopy({ ...dataCopy, ...updatedPiece });
                  }}>
                  {
                    [
                      {"key" : "k_lms", "text" : "k_lms"},
                      {"key" : "ddim", "text" : "ddim"},
                      {"key" : "plms", "text" : "plms"},
                      {"key" : "k_euler", "text" : "k_euler"},
                      {"key" : "k_euler_ancestral", "text" : "k_euler_ancestral"},
                      {"key" : "k_heun", "text" : "k_heun"},
                      {"key" : "k_dpm_2", "text" : "k_dpm_2"},
                      {"key" : "k_dpm_2_ancestral", "text" : "k_dpm_2_ancestral"},
                    ].map(shape=>{
                      return <option key = {shape.key} value={shape.key}>{shape.text}</option>
                    })
                  }
                </Select>
              </FormControl>
            </WrapItem>
            <WrapItem>
                <FormControl>
                <FormLabel htmlFor="steps">Steps</FormLabel>
                <NumberInput
                  id="steps"
                  value={dataCopy.params.steps}
                  min={10}
                  max={150}
                  clampValueOnBlur={true}
                  onChange={(value) => {
                    let updatedPiece = JSON.parse(JSON.stringify(dataCopy));
                    updatedPiece.params.steps = parseInt(value);
                    setDataCopy({ ...dataCopy, ...updatedPiece });
                  }}
                >
                  <NumberInputField />
                  <NumberInputStepper>
                    <NumberIncrementStepper />
                    <NumberDecrementStepper />
                  </NumberInputStepper>
                </NumberInput>
                </FormControl>
              </WrapItem>
              <WrapItem>
                <FormControl>
                <FormLabel htmlFor="scale">
                  Scale
                </FormLabel>
                <NumberInput
                  id="scale"
                  value={dataCopy.params.scale}
                  precision={2}
                  step={0.1}
                  min={1}
                  max={15}
                  onChange={(value) => {
                    let updatedPiece = JSON.parse(JSON.stringify(dataCopy));
                    updatedPiece.params.scale = parseFloat(value);
                    setDataCopy({ ...dataCopy, ...updatedPiece });
                  }}
                >
                  <NumberInputField />
                  <NumberInputStepper>
                    <NumberIncrementStepper />
                    <NumberDecrementStepper />
                  </NumberInputStepper>
                </NumberInput>
              </FormControl>
              </WrapItem>
            </Wrap>
              <Wrap>
              <WrapItem>
                <FormControl>
                  <FormLabel htmlFor="width">Width</FormLabel>
                  <NumberInput
                    id="width"
                    step={64}
                    value={dataCopy.params.width_height?dataCopy.params.width_height[0]:1280}
                    min={128}
                    max={2560}
                    clampValueOnBlur={true}
                    onChange={(value) => {
                      let updatedPiece = JSON.parse(JSON.stringify(dataCopy))
                      updatedPiece.params.width_height[0] = parseInt(value)
                      setDataCopy({ ...dataCopy, ...updatedPiece });
                    }}
                  >
                    <NumberInputField />
                    <NumberInputStepper>
                      <NumberIncrementStepper/>
                      <NumberDecrementStepper/>
                    </NumberInputStepper>
                  </NumberInput>
                </FormControl>
              </WrapItem>
              <WrapItem>
                <FormControl>
                  <FormLabel htmlFor="height">Height</FormLabel>
                  <NumberInput
                    id="height"
                    step={64}
                    value={dataCopy.params.width_height?dataCopy.params.width_height[1]:768}
                    min={128}
                    max={2560}
                    clampValueOnBlur={true}
                    onChange={(value) => {
                      let updatedPiece = JSON.parse(JSON.stringify(dataCopy))
                      updatedPiece.params.width_height[1] = parseInt(value)
                      setDataCopy({ ...dataCopy, ...updatedPiece });
                    }}
                  >
                    <NumberInputField />
                    <NumberInputStepper>
                      <NumberIncrementStepper/>
                      <NumberDecrementStepper/>
                    </NumberInputStepper>
                  </NumberInput>
                </FormControl>
              </WrapItem>
              {/* <WrapItem>
                <FormControl>
                <FormLabel htmlFor="eta">ETA</FormLabel>
                <NumberInput
                  id="eta"
                  step={0.1}
                  precision={2}
                  value={dataCopy.params.eta}
                  min={0.0}
                  max={10}
                  onChange={(value) => {
                    let updatedPiece = JSON.parse(JSON.stringify(dataCopy));
                    updatedPiece.params.eta = parseFloat(value);
                    setDataCopy({ ...dataCopy, ...updatedPiece });
                  }}
                >
                  <NumberInputField />
                  <NumberInputStepper>
                    <NumberIncrementStepper />
                    <NumberDecrementStepper />
                  </NumberInputStepper>
                </NumberInput>
              </FormControl>
              </WrapItem> */}
            </Wrap>
            <Wrap>
            </Wrap>
            {/* <Wrap>
              {tags && tags.map((tag)=>{
                return (<Checkbox key={tag.tag}>{tag.tag  }</Checkbox>)
              })}
            </Wrap> */}
            </ModalBody>
            <ModalFooter>
            <Button variant='ghost' colorScheme='red' mr={3} onClick={onClose}>
              Cancel
            </Button>
            <Button colorScheme={"blue"} onClick={save}>Create</Button>
            </ModalFooter>
            </>
          }
      </ModalContent>
    </Modal>
    </>
  );
}
